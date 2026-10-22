# Restauración de pedidos

Restaurar la base de pedidos solo puede hacerlo alguien con el rol `plataforma-oncall`. El objetivo de tiempo es 45 minutos desde que se abre el ticket `NORTE-RESTORE`.

La restauración ocurre en el clúster `norte-restore`. Está prohibido volcar un snapshot encima de producción. El primer lunes de cada mes, a las 11:00 UTC, la guardia ejecuta un ensayo con el semanal más reciente.

Checklist del ensayo:

1. Abrir el ticket `NORTE-RESTORE`.
2. Elegir el semanal vigente en `norte-frio-baq`.
3. Restaurar en `norte-restore`.
4. Verificar el checksum contra el manifiesto.
5. Contar las filas de la tabla `pedidos` y compararlas con el manifiesto.
6. Cerrar el ticket con la duración real. Si pasa de 45 minutos, el ensayo se marca como fallido.
