"""Catálogo de eventos. Día 0 = primera rueda en que el mercado pudo reaccionar.

Cada evento lleva su fuente. Solo entran hechos con fecha cierta; los procesos graduales
(la suba del riesgo país en octubre 2026, la guerra con Irán) se tratan como factores,
no como eventos.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Evento:
    dia0: str
    pais: str          # "AR", "BR" o "Global"
    nombre: str
    hecho: str
    fuente: str


EVENTOS = [
    Evento("2023-12-11", "AR", "Asume Milei", "Asunción presidencial el domingo 10/12/2023",
           "Boletín Oficial"),
    Evento("2023-12-13", "AR", "Devaluación", "Caputo anuncia devaluación del oficial a $800 la noche del 12/12",
           "Ministerio de Economía"),
    Evento("2024-11-27", "BR", "Paquete fiscal Haddad", "Se filtra el 27/11 que el recorte de gasto viene con exención de Ganancias; el real supera 6 por dólar",
           "Ministério da Fazenda"),
    Evento("2025-04-03", "Global", "Aranceles de Trump", "Anuncio de aranceles recíprocos el 2/4/2025 tras el cierre",
           "Casa Blanca"),
    Evento("2025-04-14", "AR", "Salida del cepo", "Acuerdo con el FMI y bandas cambiarias anunciados el viernes 11/4/2025",
           "BCRA / FMI"),
    Evento("2025-09-08", "AR", "Derrota en Buenos Aires", "El peronismo gana la elección bonaerense del domingo 7/9/2025",
           "Junta Electoral PBA"),
    Evento("2025-09-22", "AR", "Respaldo del Tesoro de EEUU", "Bessent anuncia que EEUU hará 'lo necesario' para apoyar a Argentina",
           "Tesoro de EEUU"),
    Evento("2025-10-27", "AR", "Triunfo en legislativas", "La Libertad Avanza gana las legislativas del domingo 26/10/2025",
           "Dirección Nacional Electoral"),
    Evento("2026-10-05", "BR", "1ª vuelta: Flávio adelante", "Flávio Bolsonaro 47,0% vs Lula 45,2% el domingo 4/10/2026",
           "TSE; Chequeado"),
    Evento("2026-10-26", "BR", "Lula reelecto", "Lula gana el balotaje del domingo 25/10/2026 con 51,8%",
           "TSE; Wikipedia"),
]
