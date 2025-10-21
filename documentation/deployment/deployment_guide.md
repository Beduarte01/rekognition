# Guía de Despliegue - Rekognition Proctoring

## Estructura Final del Proyecto

```
proyecto/
├── dev/
│   ├── config.json
│   ├── local_utils.py
│   └── main.py
├── documentation/
│   ├── deployment/
│   │   ├── commands.md
│   │   └── deployment_guide.md
│   └── development/
│       └── rekognition_document.docx
├── src/
│   ├── config.py
│   ├── handler.py
│   └── utils.py
├── .env
├── .gitignor
├── requirements.txt
├── template.yaml
└── local_tester.py
```

## NOTA 

Si se va a trabajar de forma local sin s3 hay que crear las carpetas en la raiz del proyecto llamadas images/ - reference/ - results.
Por el contrario si se va a realizar pruebas con s3 de forma local deberás
utilizar la librería moto (mock S3) y cargar objetos con moto antes de invocar el handler.

---

### Archivos que NO se usan en Lambda (solo local):
- Al interior de la carpeta dev, los archivos:
- `main.py`
- `config.json`
- `local_utils.py`

---

## Paso 1: Configurar Variables de Entorno

Edita el archivo `.env` con tus valores reales:

```bash
# .env
AWS_REGION=us-east-1
MIN_CONFIDENCE=75
MAX_LABELS=10
IMAGES_PREFIX=images/
REFERENCE_PREFIX=reference/
RESULTS_PREFIX=results/
PROCTORING_WEBHOOK_URL=https://tu-sistema-proctoring.com/api/webhook
```

---

## Paso 2: Instalar Dependencias

```bash
# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## Paso 3: Instalar AWS SAM CLI

```bash
# En macOS
brew install aws-sam-cli

# En Windows (con Chocolatey)
choco install aws-sam-cli

# En Linux
# Ver: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
```

Verificar instalación:
```bash
sam --version
```

---

## Paso 4: Crear Bucket S3

```bash
# Reemplaza 'mi-bucket-proctoring' con tu nombre único de bucket
aws s3 mb s3://mi-bucket-proctoring --region us-east-1
```

---

## Paso 5: Subir Imagen de Referencia

```bash
# Subir imagen de referencia para un usuario
# El nombre del archivo debe ser: {user_id}.jpg
aws s3 cp ruta/local/foto_referencia.jpg s3://mi-bucket-proctoring/reference/user_456.jpg

# Verificar que se subió correctamente
aws s3 ls s3://mi-bucket-proctoring/reference/
```

---

## Paso 6: Probar Localmente (Opcional pero Recomendado)

Antes de desplegar a AWS, prueba localmente:

```bash
# Asegúrate de que tu .env esté configurado
# Asegúrate de tener credenciales AWS configuradas

# Edita local_tester.py y cambia:
# - bucket_name = "tu-bucket-proctoring"  # TU bucket real
# - exam_id, user_id según tus datos

# Ejecutar tester
python local_tester.py
```

El tester te mostrará un menú:
- Opción 1: Probar una sola imagen
- Opción 2: Probar múltiples imágenes
- Opción 3: Probar sin referencia
- Opción 4: Todas las pruebas

**IMPORTANTE**: Para que funcione, la imagen de prueba debe existir en S3:
```bash
# Subir imagen de prueba
aws s3 cp test.jpg s3://mi-bucket-proctoring/images/exam_123/user_456/capture_001.jpg
```

---

## Paso 7: Desplegar con SAM

### Primera vez (deploy guiado):

```bash
# Build del proyecto
sam build

# Deploy con configuración guiada
sam deploy --guided
```

Te preguntará:
- **Stack Name**: `proctoring-stack` (o el nombre que prefieras)
- **AWS Region**: `us-east-1`
- **Parameter BucketName**: `mi-bucket-proctoring` (tu bucket creado)
- **Parameter ProctoringWebhookUrl**: Tu URL de webhook (o dejar vacío)
- **Confirm changes before deploy**: `Y`
- **Allow SAM CLI IAM role creation**: `Y`
- **Disable rollback**: `N`
- **Save arguments to configuration file**: `Y`
- **SAM configuration file**: `samconfig.toml` (default)
- **SAM configuration environment**: `default` (default)

### Despliegues posteriores:

```bash
# Build
sam build

# Deploy (usará la configuración guardada)
sam deploy
```

---

## ✅ Paso 8: Verificar Despliegue

```bash
# Ver información del stack
aws cloudformation describe-stacks --stack-name proctoring-stack

# Ver outputs (nombre de Lambda, bucket, etc.)
aws cloudformation describe-stacks --stack-name proctoring-stack --query 'Stacks[0].Outputs'
```

---

## 🎯 Paso 9: Probar en AWS

### Subir imagen de prueba:

```bash
aws s3 cp test.jpg s3://mi-bucket-proctoring/images/exam_123/user_456/capture_001.jpg
```

Esto debería:
1. Activar automáticamente la Lambda
2. Procesar la imagen con Rekognition
3. Guardar resultado en `s3://mi-bucket-proctoring/results/exam_123/user_456/capture_001.json`
4. (Opcional) Notificar al webhook de proctoring

### Ver logs de Lambda:

```bash
# Ver logs en tiempo real
sam logs -n RekognitionFn --stack-name proctoring-stack --tail

# Ver logs de las últimas 10 minutos
sam logs -n RekognitionFn --stack-name proctoring-stack --start-time '10min ago'
```

### Verificar resultado:

```bash
# Descargar resultado
aws s3 cp s3://mi-bucket-proctoring/results/exam_123/user_456/capture_001.json resultado.json

# Ver contenido
cat resultado.json
```

Ejemplo de resultado exitoso:
```json
{
  "status": "OK",
  "details": [],
  "face": {
    "BoundingBox": {...},
    "Confidence": 99.9
  },
  "exam_id": "exam_123",
  "user_id": "user_456",
  "s3_input": "s3://mi-bucket-proctoring/images/exam_123/user_456/capture_001.jpg"
}
```

Ejemplo de alerta:
```json
{
  "status": "ALERT",
  "reason": "Face does not match reference",
  "details": [],
  "exam_id": "exam_123",
  "user_id": "user_456",
  "s3_input": "s3://mi-bucket-proctoring/images/exam_123/user_456/capture_001.jpg"
}
```

---

## Paso 10: Actualizar Lambda

Cuando hagas cambios en el código:

```bash
# 1. Modificar archivos en src/
# 2. Build
sam build

# 3. Deploy
sam deploy
```

---

## Monitoreo

### CloudWatch Logs:
```bash
# Ver logs
sam logs -n RekognitionFn --stack-name proctoring-stack --tail
```

### CloudWatch Metrics:
- Ve a AWS Console → CloudWatch → Metrics
- Busca: Lambda → By Function Name → RekognitionFn
- Métricas importantes:
  - Invocations (invocaciones)
  - Errors (errores)
  - Duration (duración)
  - Throttles (limitaciones)

---

## Limpieza (Eliminar Stack)

Para eliminar todo lo creado:

```bash
# CUIDADO: Esto eliminará la Lambda pero NO el bucket S3
sam delete --stack-name proctoring-stack

# Para eliminar el bucket (vacíalo primero):
aws s3 rm s3://mi-bucket-proctoring --recursive
aws s3 rb s3://mi-bucket-proctoring
```

---

## Troubleshooting

### Error: "No module named 'config'"
- Verifica que `src/config.py` exista
- El archivo `template.yaml` debe tener `CodeUri: src/`

### Error: "Access Denied" al leer S3
- Verifica los permisos IAM en `template.yaml`
- La Lambda debe tener permisos para `s3:GetObject` y `s3:PutObject`

### Lambda no se ejecuta al subir imagen
- Verifica que la notificación S3 esté configurada correctamente
- Ve a AWS Console → S3 → tu bucket → Properties → Event notifications
- Debe haber una notificación que apunte a tu Lambda

### Error: "Reference image not found"
- Verifica que exista `reference/{user_id}.jpg` en S3
- El `user_id` debe coincidir exactamente con el de la ruta de la imagen

### Webhook no responde
- Verifica que `PROCTORING_WEBHOOK_URL` esté correctamente configurado
- Revisa los logs de Lambda para ver errores de conexión
- El webhook debe aceptar POST con JSON

---

## Notas Importantes

1. **Convención de nombres**:
   - Imágenes: `images/{exam_id}/{user_id}/{filename}.jpg`
   - Referencias: `reference/{user_id}.jpg`
   - Resultados: `results/{exam_id}/{user_id}/{filename}.json`

2. **Costos AWS**:
   - Lambda: Free tier incluye 1M requests/mes
   - Rekognition: ~$0.001 por imagen analizada
   - S3: ~$0.023 por GB/mes

3. **Límites**:
   - Lambda timeout: 30 segundos (configurable en template.yaml)
   - Tamaño máximo imagen: 5MB para Rekognition

4. **Seguridad**:
   - No guardes credenciales AWS en el código
   - Usa variables de entorno para datos sensibles
   - El archivo `.env` NO debe subirse a Git (está en .gitignore)
   - Usa IAM roles con permisos mínimos necesarios

5. **Backup**:
   - Considera activar versionado en el bucket S3
   - Configura lifecycle policies para archivar resultados antiguos

---

## Integración con Sistema de Proctoring

### Formato del Webhook

Tu sistema de proctoring recibirá POST requests con este formato:

```json
{
  "status": "OK" | "ALERT" | "ALERT_FINAL",
  "reason": "Face does not match reference",
  "details": [...],
  "exam_id": "exam_123",
  "user_id": "user_456",
  "s3_input": "s3://bucket/images/exam_123/user_456/capture_001.jpg",
  "face": {
    "BoundingBox": {...},
    "Confidence": 99.9
  }
}
```

### Ejemplo de implementación del webhook (Node.js/Express):

```javascript
app.post('/api/webhook', async (req, res) => {
  const { status, reason, exam_id, user_id } = req.body;
  
  if (status === 'ALERT') {
    // Registrar alerta en tu base de datos
    await db.alerts.create({
      exam_id,
      user_id,
      reason,
      timestamp: new Date()
    });
    
    // Notificar al proctor en tiempo real (WebSocket, etc.)
    notifyProctor({ exam_id, user_id, reason });
  }
  
  res.json({ success: true });
});
```

---

## Optimizaciones Futuras

1. **Agregar DynamoDB** (si lo necesitas después):
   - Descomentar las secciones de DynamoDB en `template.yaml`
   - Descomentar `_maybe_ddb_put()` en `handler.py`

2. **Procesamiento por lotes**:
   - Modificar Lambda para procesar múltiples imágenes en una invocación
   - Usar SQS para cola de procesamiento

3. **Detección de movimiento avanzada**:
   - Implementar análisis de múltiples frames consecutivos
   - Almacenar historial de posiciones faciales en memoria/DynamoDB

4. **Dashboard en tiempo real**:
   - Usar API Gateway + WebSockets para notificaciones push
   - Frontend con React para visualización en tiempo real

5. **Machine Learning adicional**:
   - Detección de emociones sospechosas
   - Análisis de patrones de comportamiento
   - Custom model con SageMaker

---

## Recursos Adicionales

- [AWS Rekognition Docs](https://docs.aws.amazon.com/rekognition/)
- [AWS SAM Docs](https://docs.aws.amazon.com/serverless-application-model/)
- [Boto3 Docs](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [S3 Event Notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html)

---

## Soporte

Si tienes problemas:
1. Revisa los logs de CloudWatch
2. Verifica la configuración de IAM
3. Comprueba que las rutas S3 sigan la convención
4. Asegúrate de que las imágenes sean JPG válidas

---