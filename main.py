import json
from symbol_table import TablaSimbolos
from parser_module import analizar_archivo_entrada
from semantic import AnalizadorSemantico
from test_cases import CASOS_DE_PRUEBA

def ejecutar_todas_las_pruebas():
    tabla_simbolos = TablaSimbolos()
    analizador = AnalizadorSemantico(tabla_simbolos)
    
    resultados_totales = []
    print("=== EJECUCIÓN DE CASOS DE PRUEBA Y ANÁLISIS SEMÁNTICO ===")
    
    for tc in CASOS_DE_PRUEBA:
        print(f"\n--- Caso {tc['id']}: {tc['descripcion']} ---")
        sesiones = analizar_archivo_entrada(tc["input"])
        
        salida_caso = {
            "caso_id": tc["id"],
            "descripcion": tc["descripcion"],
            "sesiones": []
        }
        
        for ses in sesiones:
            analisis = analizador.analizar_sesion(ses)
            salida_caso["sesiones"].append(analisis)
            
            print(f"  [Sesión ID: {analisis['id']}] Estado: {analisis['estado']}")
            print(f"  Estado Análisis: {analisis['estado_analisis']}")
            print(f"  Resumen Aspectos: {analisis['resumen_aspectos']}")
            print(f"  Entidades (Tickets): {analisis['entidades']}")
            print(f"  Correcciones: {analisis['correcciones']}")
            if analisis['errores']:
                print(f"  Errores/Rechazos: {analisis['errores']}")
            print("  Trazabilidad mínima:")
            for tr in analisis['traza']:
                print(f"    Turno {tr['turno']} -> Tokens: {tr['tokens']} -> Estructura: {tr['estructura']} -> Semántica: {tr['semantica']}")
                
        resultados_totales.append(salida_caso)

    archivo_salida = "output_results.json"
    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump(resultados_totales, f, ensure_ascii=False, indent=4)
        
    print(f"\nResultados exportados exitosamente a {archivo_salida}")

if __name__ == "__main__":
    ejecutar_todas_las_pruebas()
