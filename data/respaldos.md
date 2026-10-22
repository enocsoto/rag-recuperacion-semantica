# Respaldos de la base de pedidos

La plataforma Norte respalda la base de pedidos con el job `norte-backup-pedidos`. El snapshot diario corre a las 02:10 UTC contra el nodo de solo lectura `pedidos-ro.norte.internal`. No se toma el dump desde el primario de escritura.

La herramienta es `pg_dump` en formato custom. El archivo queda en el bucket `norte-frio-baq`, bajo el prefijo `pedidos/diario/`. El snapshot diario se retiene 14 días. El domingo a las 03:00 UTC el mismo job publica además una copia semanal en `pedidos/semanal/`, y esa copia se retiene 90 días.

El caché Redis de sesiones no se respalda. Si se pierde, la plataforma lo reconstruye al iniciar sesión. Los logs de aplicación tampoco entran en este job.

Si el job supera 25 minutos, alerta en el canal `#norte-guardia`. El manifiesto del dump incluye el checksum, la hora de inicio y la cantidad de filas de la tabla `pedidos`. Sin manifiesto, el archivo no se considera válido.

Procedimiento del operador:

1. Confirmar que el nodo `pedidos-ro.norte.internal` acepta conexiones de solo lectura.
2. Lanzar `norte-backup-pedidos` y anotar la hora de inicio.
3. Esperar el manifiesto en `pedidos/diario/`.
4. Comparar el checksum del archivo con el del manifiesto.
5. Verificar que la retención diaria no deje más de 14 snapshots.
6. Si es domingo, confirmar la copia en `pedidos/semanal/`.
7. Si el job pasa de 25 minutos, avisar en `#norte-guardia` y no relanzar encima del mismo archivo.
8. Cerrar el turno dejando el id del snapshot en la bitácora de plataforma.

Notas de operación:

El operador no interrumpe un dump a mitad de camino. Si falla el checksum, se borra ese archivo y se lanza el job otra vez. El nombre del archivo lleva la fecha UTC. Un snapshot de martes no reemplaza al de lunes. La bitácora guarda el id, la hora de fin y el resultado del checksum. El canal `#norte-guardia` recibe un mensaje verde cuando el manifiesto queda escrito. Un mensaje rojo significa que el job pasó de 25 minutos o que el checksum no coincide. En ese caso no se publica copia semanal, aunque sea domingo. El nodo `pedidos-ro.norte.internal` se usa solo para este job y para consultas de soporte. Nadie restaura desde ese nodo. El bucket `norte-frio-baq` rechaza un upload sin manifiesto. El prefijo `pedidos/diario/` conserva como máximo 14 objetos. El prefijo `pedidos/semanal/` conserva como máximo 90 días de copias. Redis queda fuera. Loki queda fuera. VictoriaMetrics queda fuera. Esos sistemas tienen su propia retención y no entran en `norte-backup-pedidos`.
