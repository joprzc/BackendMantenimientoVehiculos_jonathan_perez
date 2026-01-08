from django.contrib import messages

# Los mixins se usan cuando repites lógica como:
# Mensajes de éxito/error,
# Redirecciones según rol,
# Validaciones comunes,

# class SuccessMessageMixin:
#     success_message = ""

#     def form_valid(self, form):
#         messages.success(self.request, self.success_message)
#         return super().form_valid(form)
