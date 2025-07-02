# Comandos curl para probar Azure Durable Functions E/M Coding API

## 1. Health Check
```bash
curl -X GET http://localhost:7071/api/health
```

## 2. Iniciar procesamiento de documento individual
```bash
curl -X POST http://localhost:7071/api/start_em_coding \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "TEST-001",
    "date_of_service": "2024-01-15",
    "provider": "Dr. John Smith",
    "text": "Patient presents for routine follow-up of osteoarthritis. Chief complaint: mild right knee pain, stable. History of present illness: 65-year-old patient with known osteoarthritis of the right knee returns for routine follow-up. Reports mild, persistent pain rated 3/10. Pain is worse with prolonged standing and walking. No recent injuries or changes in symptoms. Physical examination: Constitutional: Patient appears well, no acute distress. Vital signs stable. Musculoskeletal: Right knee examination reveals mild crepitus with range of motion. No significant swelling, warmth, or erythema. Range of motion slightly limited compared to contralateral side. Gait steady. Assessment and Plan: Osteoarthritis of right knee, stable. Continue current treatment regimen including NSAIDs as needed and physical therapy. Patient counseled on joint protection techniques. Return in 3 months or sooner if symptoms worsen."
  }'
```

## 3. Verificar estado de orquestación (reemplaza INSTANCE_ID con el ID real)
```bash
curl -X GET http://localhost:7071/api/check_status/INSTANCE_ID
```

## 4. Procesamiento en lote
```bash
curl -X POST http://localhost:7071/api/batch_em_coding \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "document_id": "BATCH-001",
        "date_of_service": "2024-01-15",
        "provider": "Dr. Jane Wilson",
        "text": "Patient presents with acute exacerbation of chronic low back pain. Chief complaint: severe lower back pain radiating to left leg. History: 45-year-old construction worker with history of lumbar disc herniation. Current episode began 3 days ago after lifting heavy equipment. Pain rated 8/10, shooting down left leg to knee. Physical exam: Constitutional: Patient in moderate distress due to pain. Musculoskeletal: Lumbar spine tender to palpation L4-L5 region. Positive straight leg raise test on left. Decreased sensation over L5 dermatome. Reflexes diminished at left ankle. Assessment: Acute exacerbation of lumbar disc herniation with radiculopathy. Plan: MRI lumbar spine, referral to orthopedic spine specialist, prescribe muscle relaxants and anti-inflammatories."
      },
      {
        "document_id": "BATCH-002",
        "date_of_service": "2024-01-16",
        "provider": "Dr. Michael Chen",
        "text": "Patient presents for post-operative follow-up after arthroscopic knee surgery. Chief complaint: routine post-op check, healing well. History: 28-year-old athlete, 2 weeks post arthroscopic meniscectomy of right knee. No complications during surgery. Physical exam: Constitutional: Well-appearing, no acute distress. Musculoskeletal: Right knee surgical sites clean, dry, intact. No signs of infection. Range of motion improving, currently 0-90 degrees flexion. Minimal swelling, no warmth or erythema. Assessment: Healing well post arthroscopic meniscectomy. Plan: Continue physical therapy, advance weight-bearing as tolerated, return in 2 weeks."
      }
    ]
  }'
```

## 5. Probar con PDFs de muestra
```bash
curl -X GET "http://localhost:7071/api/test_samples?limit=2"
```

## Flujo típico de prueba:

1. **Iniciar Azure Functions**:
```bash
func start
```

2. **Health Check**:
```bash
curl -X GET http://localhost:7071/api/health
```

3. **Iniciar procesamiento**:
```bash
RESPONSE=$(curl -s -X POST http://localhost:7071/api/start_em_coding \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "TEST-001",
    "date_of_service": "2024-01-15",
    "provider": "Dr. Test",
    "text": "Patient presents with mild knee pain, stable condition."
  }')

echo $RESPONSE
```

4. **Extraer Instance ID** (usando jq):
```bash
INSTANCE_ID=$(echo $RESPONSE | jq -r '.instance_id')
echo "Instance ID: $INSTANCE_ID"
```

5. **Verificar estado periódicamente**:
```bash
curl -X GET http://localhost:7071/api/check_status/$INSTANCE_ID
```

6. **Monitorear hasta completar**:
```bash
while true; do
  STATUS=$(curl -s -X GET http://localhost:7071/api/check_status/$INSTANCE_ID | jq -r '.runtime_status')
  echo "Status: $STATUS"
  if [[ "$STATUS" == "Completed" || "$STATUS" == "Failed" ]]; then
    break
  fi
  sleep 5
done
```

7. **Obtener resultado final**:
```bash
curl -s -X GET http://localhost:7071/api/check_status/$INSTANCE_ID | jq '.output'
```

## Scripts útiles:

### Script para monitorear automáticamente:
```bash
#!/bin/bash
monitor_orchestration() {
  local instance_id=$1
  echo "Monitoring orchestration: $instance_id"
  
  while true; do
    response=$(curl -s -X GET "http://localhost:7071/api/check_status/$instance_id")
    status=$(echo "$response" | jq -r '.runtime_status')
    
    echo "$(date): Status = $status"
    
    if [[ "$status" == "Completed" ]]; then
      echo "✅ Orchestration completed successfully!"
      echo "$response" | jq '.output'
      break
    elif [[ "$status" == "Failed" ]]; then
      echo "❌ Orchestration failed!"
      echo "$response" | jq '.'
      break
    fi
    
    sleep 5
  done
}

# Uso: monitor_orchestration "instance-id-here"
```

### Script para probar batch completo:
```bash
#!/bin/bash
echo "🚀 Starting batch test..."

# Iniciar batch
batch_response=$(curl -s -X POST http://localhost:7071/api/batch_em_coding \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "document_id": "BATCH-001",
        "date_of_service": "2024-01-15",
        "provider": "Dr. Test",
        "text": "First test document with mild symptoms."
      },
      {
        "document_id": "BATCH-002",
        "date_of_service": "2024-01-16",
        "provider": "Dr. Test",
        "text": "Second test document with moderate symptoms."
      }
    ]
  }')

echo "Batch response: $batch_response"

# Extraer instance IDs
instance_ids=$(echo "$batch_response" | jq -r '.instance_details[].instance_id')

# Monitorear cada instancia
for id in $instance_ids; do
  echo "Monitoring instance: $id"
  monitor_orchestration "$id" &
done

wait
echo "🎉 All batch operations completed!"
```
