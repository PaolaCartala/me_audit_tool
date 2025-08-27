"""
Script de diagnóstico para verificar el servidor MCP y la herramienta appointment-dictation
"""
import asyncio
import json
import os
from dotenv import load_dotenv
from settings import logger

# Load environment variables
load_dotenv()

async def diagnose_mcp_server():
    """
    Diagnóstica problemas específicos con el servidor MCP
    """
    logger.debug("🔍 DIAGNÓSTICO DEL SERVIDOR MCP")
    logger.debug("=" * 50)
    
    # 1. Verificar variables de entorno
    mcp_url = os.getenv("MCP_API_URL")
    mcp_key = os.getenv("MCP_API_KEY")
    
    logger.debug(f"MCP_API_URL: {mcp_url}")
    logger.debug(f"MCP_API_KEY: {'***' + mcp_key[-4:] if mcp_key else 'Not set'}")
    
    if not mcp_url or not mcp_key:
        logger.error("❌ Variables MCP no configuradas correctamente")
        return
    
    try:
        from pydantic_ai.mcp import MCPServerSSE
        
        # 2. Test de conexión básica
        logger.debug("\n🌐 Probando conexión al servidor MCP...")
        
        server = MCPServerSSE(url=mcp_url, headers={"X-API-Key": mcp_key})
        async with server:
            # 3. Listar herramientas disponibles
            logger.debug("🔧 Obteniendo herramientas disponibles...")
            tools = await server.list_tools()
            
            logger.debug(f"✅ Herramientas encontradas: {len(tools)}")
            for i, tool in enumerate(tools, 1):
                # Los objetos ToolDefinition tienen atributos directos, no métodos get()
                name = tool.name if hasattr(tool, 'name') else 'Unknown'
                desc = tool.description if hasattr(tool, 'description') else 'No description'
                logger.debug(f"  {i}. {name}: {desc}")
            
            # 4. Verificar si appointment-dictation existe
            appointment_tool = next((t for t in tools if hasattr(t, 'name') and t.name == 'appointment-dictation'), None)
            
            if not appointment_tool:
                logger.error("❌ Herramienta 'appointment-dictation' no encontrada")
                return
            
            logger.debug("✅ Herramienta 'appointment-dictation' encontrada")
            logger.debug(f"📋 Schema: {appointment_tool.parameters_json_schema if hasattr(appointment_tool, 'parameters_json_schema') else 'No schema'}")
            
            # 5. Test con diferentes IDs de appointment válidos
            # Estos IDs pueden no existir, vamos a probar con algunos comunes
            test_ids = [
                "175ac3cb-e718-40c7-805a-5306dcadee8a",  # Tu ID actual
                "563543C8-23FF-481B-93DE-1D2C93959DE8",   # ID alternativo del código
                "00000000-0000-0000-0000-000000000001",   # ID de prueba 1
                "11111111-1111-1111-1111-111111111111",   # ID de prueba 2
            ]
            
            for test_id in test_ids:
                logger.debug(f"\n🧪 Probando con appointment ID: {test_id}")
                try:
                    response = await server.call_tool(
                        tool_name="appointment-dictation",
                        arguments={"appointmentId": test_id}
                    )
                    logger.debug(f"✅ Éxito con ID {test_id}")
                    logger.debug(f"📄 Respuesta (preview): {str(response)[:200]}...")
                    
                    # Guardar respuesta exitosa
                    with open(f"mcp_success_{test_id[:8]}.json", "w") as f:
                        json.dump(response, f, indent=2)
                    break  # Si uno funciona, salimos del loop
                    
                except Exception as e:
                    logger.error(f"❌ Error con ID {test_id}: {str(e)}")
                    
                    # Intentar obtener más detalles del error
                    error_details = {
                        "test_id": test_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "tool_args": {"appointmentId": test_id}
                    }
                    
                    with open(f"mcp_error_{test_id[:8]}.json", "w") as f:
                        json.dump(error_details, f, indent=2)
            
            # 6. Test de otras herramientas para ver si es específico de appointment-dictation
            logger.debug("\n🔍 Probando otras herramientas disponibles...")
            
            for tool in tools:
                tool_name = tool.name if hasattr(tool, 'name') else 'Unknown'
                if tool_name != 'appointment-dictation':
                    try:
                        logger.debug(f"🧪 Probando herramienta: {tool_name}")
                        
                        # Construir argumentos basados en el schema
                        schema = tool.parameters_json_schema if hasattr(tool, 'parameters_json_schema') else {}
                        required = schema.get('required', [])
                        properties = schema.get('properties', {})
                        
                        # Crear argumentos de prueba
                        test_args = {}
                        for req_param in required:
                            if req_param in properties:
                                param_type = properties[req_param].get('type', 'string')
                                if param_type == 'string' and properties[req_param].get('format') == 'uuid':
                                    test_args[req_param] = "175ac3cb-e718-40c7-805a-5306dcadee8a"
                                elif param_type == 'string':
                                    test_args[req_param] = "test-value"
                        
                        if test_args:
                            response = await server.call_tool(tool_name=tool_name, arguments=test_args)
                            logger.debug(f"✅ {tool_name} funciona correctamente")
                        else:
                            logger.debug(f"⏭️ {tool_name} saltado (sin argumentos conocidos)")
                            
                    except Exception as e:
                        logger.error(f"❌ {tool_name} falló: {str(e)}")
    
    except Exception as e:
        logger.error(f"❌ Error general en diagnóstico MCP: {str(e)}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")

async def test_appointment_formats():
    """
    Prueba diferentes formatos de appointment ID
    """
    logger.debug("\n🔍 PROBANDO DIFERENTES FORMATOS DE APPOINTMENT ID")
    logger.debug("=" * 50)
    
    mcp_url = os.getenv("MCP_API_URL")
    mcp_key = os.getenv("MCP_API_KEY")
    
    if not mcp_url or not mcp_key:
        logger.error("❌ Variables MCP no configuradas")
        return
    
    # Diferentes formatos para probar
    test_formats = [
        "175ac3cb-e718-40c7-805a-5306dcadee8a",  # Formato original
        "175AC3CB-E718-40C7-805A-5306DCADEE8A",  # Mayúsculas
        "{175ac3cb-e718-40c7-805a-5306dcadee8a}",  # Con llaves
        "175ac3cbe71840c7805a5306dcadee8a",  # Sin guiones
    ]
    
    try:
        from pydantic_ai.mcp import MCPServerSSE
        
        server = MCPServerSSE(url=mcp_url, headers={"X-API-Key": mcp_key})
        async with server:
            for fmt in test_formats:
                logger.debug(f"🧪 Probando formato: {fmt}")
                try:
                    response = await server.call_tool(
                        tool_name="appointment-dictation",
                        arguments={"appointmentId": fmt}
                    )
                    logger.debug(f"✅ Formato {fmt} funciona!")
                    return response
                except Exception as e:
                    logger.error(f"❌ Formato {fmt} falló: {str(e)}")
    
    except Exception as e:
        logger.error(f"❌ Error en test de formatos: {str(e)}")

async def main():
    """Función principal de diagnóstico"""
    await diagnose_mcp_server()
    await test_appointment_formats()
    
    logger.debug("\n💡 RECOMENDACIONES:")
    logger.debug("1. Verificar que el appointment ID existe en la base de datos")
    logger.debug("2. Confirmar formato correcto del UUID")
    logger.debug("3. Verificar permisos de la API Key")
    logger.debug("4. Contactar al administrador del servidor MCP si persiste")

if __name__ == "__main__":
    asyncio.run(main())
