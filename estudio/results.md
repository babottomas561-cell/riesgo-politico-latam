# Resultados (generado por estudio/run.py)

Datos: 2022-06-02 a 2026-10-30.

## Retorno acumulado en USD

|      | Desde asunción de Milei   | Desde 15/7/2026   |
|:-----|:--------------------------|:------------------|
| AR   | +70.1%                    | -24.7%            |
| EWZ  | +14.2%                    | -9.9%             |
| SPY  | +70.3%                    | +0.8%             |
| MELI | +2.9%                     | -13.3%            |

## Eventos: retorno anormal acumulado [0, +1]

| Fecha      | País   | Evento                      | Argentina CAR   |   Argentina t | Brasil CAR   |   Brasil t |
|:-----------|:-------|:----------------------------|:----------------|--------------:|:-------------|-----------:|
| 2023-12-11 | AR     | Asume Milei                 | +2.7%           |           0.7 | -1.6%        |       -0.7 |
| 2023-12-13 | AR     | Devaluación                 | -3.9%           |          -1   | +2.2%        |        1   |
| 2024-11-27 | BR     | Paquete fiscal Haddad       | +0.0%           |           0   | -8.1%        |       -5   |
| 2025-04-03 | Global | Aranceles de Trump          | +5.4%           |           1.5 | +1.1%        |        0.6 |
| 2025-04-14 | AR     | Salida del cepo             | +6.3%           |           1.8 | -0.5%        |       -0.3 |
| 2025-09-08 | AR     | Derrota en Buenos Aires     | -20.5%          |          -5.7 | -0.7%        |       -0.4 |
| 2025-09-22 | AR     | Respaldo del Tesoro de EEUU | +13.6%          |           3.8 | +1.1%        |        0.6 |
| 2025-10-27 | AR     | Triunfo en legislativas     | +31.4%          |           7.1 | +0.8%        |        0.4 |
| 2026-10-05 | BR     | 1ª vuelta: Flávio adelante  | +4.7%           |           1.1 | +10.6%       |        5.3 |
| 2026-10-26 | BR     | Lula reelecto               | -8.3%           |          -2   | -23.1%       |      -10.3 |

## Atribución de la caída desde el 15/7/2026 (puntos log)

Betas: {'SPY': 1.43, 'BZ=F': 0.03, '^TNX': 0.33, 'Brasil': 0.58}, R² 0.34, 173 ruedas.

|                         |   Acciones globales (S&P 500) |   Petróleo (Brent) |   Tasa a 10 años EEUU |   Brasil (propio) |   Argentina (propio) |   total |
|:------------------------|------------------------------:|-------------------:|----------------------:|------------------:|---------------------:|--------:|
| 2025-11-03 a 2026-07-14 |                           1.1 |                0.8 |                   0.1 |              -8.2 |                -22.2 |   -28.4 |
| 2024-01-02 a 2026-07-14 |                           1   |                2.4 |                  -0.9 |              -3.6 |                -27.3 |   -28.4 |
| 2025-07-15 a 2026-07-14 |                           1.3 |                1   |                   1.4 |              -7.6 |                -24.4 |   -28.4 |
| 2026-01-02 a 2026-07-14 |                           1.1 |                0.8 |                   0.3 |              -8.6 |                -21.9 |   -28.4 |

## Reelección de Lula: corte transversal

| ticker   |   beta_brasil | ret_lula   | grupo     |
|:---------|--------------:|:-----------|:----------|
| MELI     |          0.33 | -7.8%      | MELI      |
| YPF      |          0.42 | -2.8%      | Argentina |
| PAM      |          0.5  | -3.6%      | Argentina |
| IRS      |          0.57 | -2.7%      | Argentina |
| TEO      |          0.57 | -7.4%      | Argentina |
| TGS      |          0.61 | -4.8%      | Argentina |
| GGAL     |          0.62 | -6.8%      | Argentina |
| CRESY    |          0.64 | -5.8%      | Argentina |
| EDN      |          0.67 | -5.6%      | Argentina |
| CEPU     |          0.67 | -4.5%      | Argentina |
| BMA      |          0.67 | -6.3%      | Argentina |
| LOMA     |          0.77 | -3.6%      | Argentina |
| PBR      |          0.85 | -14.0%     | Brasil    |
| NU       |          0.86 | -17.0%     | Brasil    |
| BBAR     |          0.89 | -8.0%      | Argentina |
| SUPV     |          0.93 | -9.4%      | Argentina |
| ITUB     |          1.12 | -20.4%     | Brasil    |

Beta rodante a Brasil: promedio 2025 0.41, septiembre 2026 0.80, último 0.44.
