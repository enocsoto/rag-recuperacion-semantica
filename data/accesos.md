# Accesos al bucket de respaldos

Entrar al bucket `norte-frio-baq` exige MFA. Las claves rotan cada 60 días y viven en el vault `norte/backup`. No se guardan en el repositorio ni en el chat de guardia.

La cuenta `norte-root` está prohibida para este flujo. El permiso de lectura que recibe `plataforma-oncall` expira a las 8 horas. Si hace falta más tiempo, se pide otro permiso; no se extiende el anterior.
