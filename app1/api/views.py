# seguridad básica con header X-INGEST-KEY.
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission

from .serializers import OBDIngestSerializer
from app1.services.obd_ingest import insert_obd_row


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

    def post(self, request):
        ser = OBDIngestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payload = ser.validated_data

        # anti-replay simple: timestamp no debe definir demasiado(por si el reloj del cliente está mal)
        max_skew = getattr(settings, "OBD_INGEST_MAX_SKEW_SECONDS", 300)
        ts = payload["timestamp"]
        skew = abs((timezone.now() - ts).total_seconds())
        if skew > max_skew:
            return Response(
                # {
                #     "detail": f"Timestamp fuera de rango (skew {int(skew)}s > {max_skew}s)"
                # },
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
