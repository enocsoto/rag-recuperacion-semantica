# Retención

Los snapshots diarios de pedidos viven 14 días. Los semanales viven 90 días en `norte-frio-baq`. Pasado ese plazo, el ciclo de vida del bucket los borra solo.

Los logs de aplicación viven 7 días en Loki y no se copian al bucket. Las métricas viven 30 días en VictoriaMetrics. Borrar un snapshot antes de tiempo exige un ticket firmado por dos personas de plataforma. Una sola firma no alcanza.
