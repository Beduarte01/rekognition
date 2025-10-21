# 🛠️ Comandos Útiles - Rekognition Proctoring

## 📦 Setup Inicial

```bash
# Clonar/crear proyecto
cd tu-proyecto

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar AWS SAM CLI (una sola vez)
brew install aws-sam-cli  # macOS
```

---

## 🪣 Gestión de S3

### Crear bucket
```bash
aws s3 mb s3://mi-bucket-proctoring --region us-east-1
```

### Subir imagen de referencia
```bash
# Subir para un usuario específico
aws s3 cp foto_usuario.jpg s3://mi-bucket-proctoring/reference/user_456.jpg

# Subir múltiples referencias
aws s3 cp reference_local/ s3://mi-bucket-proctoring/reference/ --recursive
```

### Subir imagen de prueba
```bash
# Una imagen
aws s3 cp test.jpg s3://mi-bucket-proctoring/images/exam_123/user_456/capture_001.jpg

# Múltiples imágenes
aws s3 cp images_local/ s3://mi-bucket-proctoring/images/exam_123/user_456/ --recursive
```

### Listar archivos
```bash
# Ver todas las referencias
aws s3 ls s3://mi-bucket-proctoring/reference/

# Ver imágenes de un examen
aws s3 ls s3://mi-bucket-proctoring/images/exam_123/user_456/

# Ver resultados
aws s3 ls s3://mi-bucket-proctoring/results/exam_123/user_456/
```

### Descargar resultados
```bash
# Un resultado específico
aws s3 cp s3://mi-bucket-proctoring/results/exam_123/user_456/capture_001.json resultado.json

# Todos los resultados de un usuario
aws s3 cp s3://mi-bucket-proctoring/results/exam_123/user_456/ resultados_local/ --recursive

# Ver resultado directamente en consola
aws s3 cp s3://mi-bucket-proctoring/results/exam_123/user_456/latest.json - | jq .
```

### Limpiar bucket
```bash
# Eliminar imágenes de un examen
aws s3 rm s3://mi-bucket-proctoring/images/exam_123/ --recursive

# Eliminar resultados de un examen
aws s3 rm s3://mi-bucket-proctoring/results/exam_123/ --recursive

# Vaciar bucket completo (CUIDADO)
aws s3 rm s3://mi-bucket-proctoring --recursive
```

---

## 🚀 Despliegue con SAM

### Primer despliegue
```bash
# Build
sam build

# Deploy guiado (primera vez)
sam deploy --guided
```

### Despliegues posteriores
```bash
# Build y deploy
sam build && sam deploy

# Solo deploy (si no cambiaste código)
sam deploy
```

### Deploy con parámetros específicos
```bash
sam deploy \
  --stack-name proctoring-stack \
  --parameter-overrides \
    BucketName=mi-bucket-proctoring \
    ProctoringWebhookUrl=https://mi-webhook.com/api
```

### Ver información del stack
```bash
# Estado general
aws cloudformation describe-stacks --stack-name proctoring-stack

# Solo outputs
aws cloudformation describe-stacks \
  --stack-name proctoring-stack \
  --query 'Stacks[0].Outputs' \
  --output table

# Recursos creados
aws cloudformation list-stack-resources --stack-name proctoring-stack
```

---

## 📊 Logs y Monitoreo

### Ver logs en tiempo real
```bash
# Tail logs (tiempo real)
sam logs -n RekognitionFn --stack-name proctoring-stack --tail

# Con filtro por texto
sam logs -n RekognitionFn --stack-name proctoring-stack --tail --filter "ERROR"
```

### Ver logs históricos
```bash
# Últimos 10 minutos
sam logs -n RekognitionFn --stack-name proctoring-stack --start-time '10min ago'

# Última hora
sam logs -n RekognitionFn --stack-name proctoring-stack --start-time '1h ago'

# Por rango de tiempo
sam logs -n RekognitionFn --stack-name proctoring-stack \
  --start-time '2024-01-01T10:00:00' \
  --end-time '2024-01-01T11:00:00'
```

### Ver métricas de Lambda
```bash
# Número de invocaciones (última hora)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=proctoring-stack-RekognitionFn-XXX \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Errores
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=proctoring-stack-RekognitionFn-XXX \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

## 🧪 Testing Local

### Ejecutar tester interactivo
```bash
python local_tester.py
```

### Ejecutar test directo con Python
```bash
# Test rápido sin menú
python -c "
from local_tester import test_single_image
test_single_image()
"
```

### Verificar configuración
```bash
# Ver variables de entorno cargadas
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('AWS_REGION:', os.getenv('AWS_REGION'))
print('PROCTORING_WEBHOOK_URL:', os.getenv('PROCTORING_WEBHOOK_URL'))
"
```

---

## 🔧 Desarrollo y Debug

### Invocar Lambda localmente con SAM
```bash
# Crear evento de prueba
cat > event.json << EOF
{
  "Records": [
    {
      "s3": {
        "bucket": {"name": "mi-bucket-proctoring"},
        "object": {"key": "images/exam_123/user_456/capture_001.jpg"}
      }
    }
  ]
}
EOF

# Invocar localmente
sam local invoke RekognitionFn -e event.json
```

### Ejecutar API local (si añades API Gateway)
```bash
sam local start-api
```

### Validar template.yaml
```bash
# Validar sintaxis
sam validate

# Validar con Linter (más estricto)
sam validate --lint
```

### Ver código empaquetado
```bash
# Ver qué se empaquetará
sam build --use-container

# Ver contenido del build
ls -la .aws-sam/build/RekognitionFn/
```

---

## 🔐 Gestión de Credenciales

### Configurar perfil AWS
```bash
# Configurar credenciales
aws configure

# Usar perfil específico
export AWS_PROFILE=mi-perfil
aws s3 ls  # Usará mi-perfil

# Ver perfil actual
aws sts get-caller-identity
```

### Variables de entorno para credenciales
```bash
# Exportar temporalmente
export AWS_ACCESS_KEY_ID=tu_access_key
export AWS_SECRET_ACCESS_KEY=tu_secret_key
export AWS_REGION=us-east-1
```

---

## 🧹 Limpieza

### Eliminar stack completo
```bash
# Eliminar Lambda, permisos, etc. (NO elimina S3)
sam delete --stack-name proctoring-stack

# Eliminar con confirmación
sam delete --stack-name proctoring-stack --no-prompts
```

### Eliminar bucket S3
```bash
# Vaciar bucket primero
aws s3 rm s3://mi-bucket-proctoring --recursive

# Eliminar bucket
aws s3 rb s3://mi-bucket-proctoring

# Todo en un comando (CUIDADO)
aws s3 rb s3://mi-bucket-proctoring --force
```

---

## 📝 Gestión de Configuración

### Actualizar variables de entorno en Lambda
```bash
# Actualizar una variable
aws lambda update-function-configuration \
  --function-name proctoring-stack-RekognitionFn-XXX \
  --environment "Variables={MIN_CONFIDENCE=80,MAX_LABELS=15}"

# Ver configuración actual
aws lambda get-function-configuration \
  --function-name proctoring-stack-RekognitionFn-XXX \
  --query 'Environment'
```

### Actualizar timeout de Lambda
```bash
aws lambda update-function-configuration \
  --function-name proctoring-stack-RekognitionFn-XXX \
  --timeout 60
```

### Actualizar memoria de Lambda
```bash
aws lambda update-function-configuration \
  --function-name proctoring-stack-RekognitionFn-XXX \
  --memory-size 1024
```

---

## 🔄 CI/CD (Automatización)

### Script de deploy rápido
```bash
#!/bin/bash
# deploy.sh

echo "🔨 Building..."
sam build

echo "🚀 Deploying..."
sam deploy

echo "✅ Deployment complete!"
sam logs -n RekognitionFn --stack-name proctoring-stack --tail
```

### Script de test completo
```bash
#!/bin/bash
# test.sh

echo "📸 Uploading test image..."
aws s3 cp test.jpg s3://mi-bucket-proctoring/images/exam_test/user_test/test_$(date +%s).jpg

echo "⏳ Waiting 5 seconds..."
sleep 5

echo "📄 Checking results..."
aws s3 ls s3://mi-bucket-proctoring/results/exam_test/user_test/

echo "📊 Latest result:"
aws s3 cp s3://mi-bucket-proctoring/results/exam_test/user_test/latest.json - | jq .
```

---

## 🎯 Comandos de Producción

### Healthcheck rápido
```bash
# Verificar que todo funciona
bash -c '
echo "🔍 Checking Lambda..."
aws lambda get-function --function-name proctoring-stack-RekognitionFn-XXX > /dev/null && echo "✅ Lambda OK" || echo "❌ Lambda ERROR"

echo "🔍 Checking S3..."
aws s3 ls s3://mi-bucket-proctoring > /dev/null && echo "✅ S3 OK" || echo "❌ S3 ERROR"

echo "🔍 Checking recent invocations..."
sam logs -n RekognitionFn --stack-name proctoring-stack --start-time "5min ago" | grep -q "REPORT" && echo "✅ Lambda invoked recently" || echo "⚠️  No recent invocations"
'
```

### Backup de configuración
```bash
# Exportar template actual
aws cloudformation get-template \
  --stack-name proctoring-stack \
  --query 'TemplateBody' \
  > backup_template_$(date +%Y%m%d).json
```

---

## 💡 Tips y Trucos

### Ver tamaño de objetos S3
```bash
# Tamaño total del bucket
aws s3 ls s3://mi-bucket-proctoring --recursive --summarize | grep "Total Size"

# Tamaño por prefijo
aws s3 ls s3://mi-bucket-proctoring/images/ --recursive --summarize | grep "Total Size"
```

### Monitorear costos
```bash
# Ver costos del mes actual (requiere Cost Explorer habilitado)
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://filter.json
```

### Alias útiles
```bash
# Agregar a ~/.bashrc o ~/.zshrc
alias sam-build='sam build'
alias sam-deploy='sam build && sam deploy'
alias sam-logs='sam logs -n RekognitionFn --stack-name proctoring-stack --tail'
alias s3-results='aws s3 ls s3://mi-bucket-proctoring/results/ --recursive'
```

---