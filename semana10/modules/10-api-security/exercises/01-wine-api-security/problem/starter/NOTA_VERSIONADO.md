# Nota de versionado: Wine Quality API 2.0.0

La API pasa de `1.1.0` a `2.0.0` porque exigir la cabecera `X-API-Key` en
`POST /v1/predictions` rompe a los clientes anónimos de 1.x: una petición que
antes devolvía `200` ahora devuelve `401`. Es un cambio incompatible, así que
según el versionado semántico toca subir la versión mayor. Los payloads, el
sobre de error y el `request_id` no cambian.

Para seguir funcionando, el front de S7 tiene que enviar `X-API-Key` con una
clave del cliente `front` (scope `predict`) en cada predicción. Además debe
tratar los nuevos códigos: `401` y `403` como un problema de configuración
del que avisar al equipo técnico, y `429` esperando los segundos de
`Retry-After`. Si se usa desde un navegador, su origen tiene que estar en
`WINE_API_CORS_ORIGINS`.

La clave se guardaría en la configuración del servidor del front: en `.env`
en local (ignorado por Git) y como variable de entorno o secreto de la
plataforma en producción. Nunca en el código ni en el navegador del usuario.
