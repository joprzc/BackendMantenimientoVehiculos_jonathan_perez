# seguridad básica con header X-INGEST-KEY.
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.parsers import JSONParser

from .serializers import OBDIngestSerializer
from app1.services.obd_ingest import insert_obd_row

from rest_framework.permissions import (
    AllowAny,
    BasePermission,
    IsAuthenticated,
)


class HasIngestKey(BasePermission):
    """
    Permite si viene el header correcto:
    X-INGEST-KEY: <proyecto_mantenimiento_key>
    """

    def has_permission(self, request, view):
        expected = getattr(settings, "OBD_INGEST_API_KEY", "")
        if not expected:
            return False  # no hay clave configurada, denegar todo
        provided = request.headers.get("X-INGEST-KEY", "")
        return provided == expected


class OBDIngestAPIView(APIView):
    permission_classes = [HasIngestKey]
    parser_classes = [JSONParser]

    def post(self, request):
        if "json" not in (request.content_type or ""):
            return Response(
                {"detail": "Envia Content-Type: application/json"},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        ser = OBDIngestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payload = ser.validated_data

        # anti-replay simple: timestamp no debe definir demasiado(por si el reloj del cliente está mal)
        max_skew = getattr(settings, "OBD_INGEST_MAX_SKEW_SECONDS", 300)
        ts = payload["timestamp"]
        skew = abs((timezone.now() - ts).total_seconds())

        # Allow historical/demo timestamps ONLY in DEBUG and when X-DEMO header is set
        is_demo = request.headers.get("X-DEMO") == "1"

        if skew > max_skew:
            # return Response(
            #     # {
            #     #     "detail": f"Timestamp fuera de rango (skew {int(skew)}s > {max_skew}s)"
            #     # },
            #     {
            #         "detail": f"Timestamp fuera de rango (skew {int(skew)}s > {max_skew}s)"
            #     },
            #     status=status.HTTP_400_BAD_REQUEST,
            # )
            if getattr(settings, "DEBUG", False) and is_demo:
                print(f"[ingest] DEMO mode: bypassing skew check ({int(skew)}s)")
            else:
                return Response(
                    {
                        "detail": f"Timestamp fuera de rango (skew {int(skew)}s > {max_skew}s)"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        print("INGEST DATA:", request.data)  # debug

        created = insert_obd_row(payload)
        return Response(
            {
                "ok": True,
                "id": created.get("id"),
                "timestamp": created.get("timestamp"),
            },
            status=status.HTTP_201_CREATED,
        )


# lista de puertos OBD
class OBDPortsAPIView(APIView):

    # No requiere auth para evitar 401 en el modal
    permission_classes = [AllowAny]

    def get(self, request):
        err = None
        try:
            import obd

            ports = obd.scan_serial() or []
        except Exception as e:

            err = str(e)
            ports = []

        # Fallback macOS: si scan_serial está vacío, listamos /dev/tty.* y /dev/cu.*
        if not ports:
            try:
                import glob

                ports = sorted(set(glob.glob("/dev/tty.*") + glob.glob("/dev/cu.*")))
            except Exception:
                pass

        include_debug = request.GET.get("include_debug") == "1"
        if not include_debug:
            ports = [p for p in ports if "debug" not in p.lower()]

        payload = {
            "ports": ports,
            "count": len(ports),
            "fallback_used": err is None and not ports,
            "error": err,
        }

        if err and not ports:
            return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(payload)


class OBDPortSelectionAPIView(APIView):
    # Permite sin autenticación para evitar 401 en el modal; la selección sólo se guarda en sesión.
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "port": request.session.get("obd_port"),
                "vehicle_id": request.session.get("obd_port_vehicle_id"),
            }
        )

    def post(self, request):
        port = (request.data.get("port") or "").strip()
        veh_id = request.data.get("vehicle_id")
        if not port:
            return Response({"detail": "El campo 'port' es requerido."}, status=400)

        request.session["obd_port"] = port
        request.session["obd_port_vehicle_id"] = veh_id
        request.session.modified = True

        return Response({"ok": True, "port": port, "vehicle_id": veh_id})
