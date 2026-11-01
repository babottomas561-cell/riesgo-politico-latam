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

| Fecha      | País   | Evento                      | Argentina CAR   |   Argentina t |   Argentina p emp | Brasil CAR   |   Brasil t |   Brasil p emp | Bonos CAR   |   Bonos t |   Bonos p emp |
|:-----------|:-------|:----------------------------|:----------------|--------------:|------------------:|:-------------|-----------:|---------------:|:------------|----------:|--------------:|
| 2023-12-11 | AR     | Asume Milei                 | +2.7%           |           0.7 |             0.458 | -1.6%        |       -0.7 |          0.402 | +0.3%       |       0.1 |         0.916 |
| 2023-12-13 | AR     | Devaluación                 | -3.9%           |          -1   |             0.305 | +2.2%        |        1   |          0.269 | +2.9%       |       0.7 |         0.373 |
| 2024-11-27 | BR     | Paquete fiscal Haddad       | +0.0%           |           0   |             1     | -8.1%        |       -5   |          0     | -0.3%       |      -0.1 |         0.855 |
| 2025-04-03 | Global | Aranceles de Trump          | +5.4%           |           1.5 |             0.129 | +1.1%        |        0.6 |          0.49  | +1.6%       |       0.8 |         0.39  |
| 2025-04-14 | AR     | Salida del cepo             | +6.3%           |           1.8 |             0.084 | -0.5%        |       -0.3 |          0.771 | +7.2%       |       3.6 |         0.004 |
| 2025-09-08 | AR     | Derrota en Buenos Aires     | -20.5%          |          -5.7 |             0     | -0.7%        |       -0.4 |          0.683 | -6.7%       |      -4.5 |         0.008 |
| 2025-09-22 | AR     | Respaldo del Tesoro de EEUU | +13.6%          |           3.8 |             0.004 | +1.1%        |        0.6 |          0.546 | +19.9%      |      12.9 |         0     |
| 2025-10-27 | AR     | Triunfo en legislativas     | +31.4%          |           7.1 |             0     | +0.8%        |        0.4 |          0.667 | +16.8%      |       6.1 |         0.004 |
| 2026-10-05 | BR     | 1ª vuelta: Flávio adelante  | +4.7%           |           1.1 |             0.189 | +10.6%       |        5.3 |          0     | +2.2%       |       0.7 |         0.116 |
| 2026-10-26 | BR     | Lula reelecto               | -8.3%           |          -2   |             0.016 | -23.1%       |      -10.3 |          0     | -2.2%       |      -1.1 |         0.084 |

p emp = fracción de ventanas de 2 días de la ventana de estimación con un residuo al menos igual.

## Atribución de la caída desde el 15/7/2026 (puntos log)

Betas: {'SPY': 1.43, 'BZ=F': 0.03, '^TNX': 0.33, 'Brasil': 0.58}, R² 0.34, 173 ruedas.

|                         |   Acciones globales (S&P 500) |   Petróleo (Brent) |   Tasa a 10 años EEUU |   Brasil (propio) |   Argentina (propio) |   total |
|:------------------------|------------------------------:|-------------------:|----------------------:|------------------:|---------------------:|--------:|
| 2025-11-03 a 2026-07-14 |                           1.1 |                0.8 |                   0.1 |              -8.2 |                -22.2 |   -28.4 |
| 2024-01-02 a 2026-07-14 |                           1   |                2.4 |                  -0.9 |              -3.6 |                -27.3 |   -28.4 |
| 2025-07-15 a 2026-07-14 |                           1.3 |                1   |                   1.4 |              -7.6 |                -24.4 |   -28.4 |
| 2026-01-02 a 2026-07-14 |                           1.1 |                0.8 |                   0.3 |              -8.6 |                -21.9 |   -28.4 |

Incertidumbre (ventana base): desvío por estimación de betas 2.3 pts; intervalo 95% del componente argentino -26.8 a -17.7. P(componente argentino < 50% de la caída) = 0.000. Contra ruido normal (17.9 pts en 77 ruedas): z = -1.2. Ventanas de 77 ruedas desde 2023 con un componente argentino igual o peor: 5.6% (peor: -64.7, el 2025-09-15).

### Bootstrap en dos etapas (re-estima también el factor Brasil; 5000 réplicas, bloques de 10)

|                       |   0.025 |   0.5 |   0.975 |   P(propio < 50%) x100 |
|:----------------------|--------:|------:|--------:|-----------------------:|
| ('AR', 'global')      |    -1.9 |   1.9 |     5.7 |                  nan   |
| ('AR', 'regional')    |   -18.9 |  -6.5 |     3.9 |                  nan   |
| ('AR', 'propio')      |   -33.3 | -23.8 |   -12   |                    5.4 |
| ('Bonos', 'global')   |    -2.4 |  -1.5 |    -0.8 |                  nan   |
| ('Bonos', 'regional') |    -3.3 |  -0.8 |     0.7 |                  nan   |
| ('Bonos', 'propio')   |   -10.6 |  -9   |    -6.8 |                    0.3 |

### Robustez a factores adicionales (AR)

|                    |   BZ=F |   Brasil |   EEM |   LatAm sin Brasil |   SPY |   ^TNX |   idiosincrático |   total |
|:-------------------|-------:|---------:|------:|-------------------:|------:|-------:|-----------------:|--------:|
| Base               |    0.8 |     -8.2 | nan   |              nan   |   1.1 |    0.1 |            -22.2 |   -28.4 |
| + Emergentes (EEM) |    1.1 |     -7.6 |  -1.4 |              nan   |   0.9 |    0.5 |            -21.8 |   -28.4 |
| + LatAm sin Brasil |    2.1 |     -4.3 | nan   |               -2.6 |   0.6 |    1.1 |            -25.3 |   -28.4 |

### Concentración del componente argentino

Total -22.2; 5 peores días -14.8; 10 peores -27.2; 10 mejores +27.9. Peor día -3.4% (2026-08-04). Días por debajo de -2 desvíos (4.1%): 0 de 77. Días negativos: 57%.

### Trayectoria del componente argentino

Acumulado al 2/10 (antes de la 1ª vuelta brasileña): -27.8 pts; al 23/10 (antes del balotaje): -27.1; final: -22.2. Brasil al 23/10: 7.7; final -8.2.

### Por sector (puntos log)

|                  |   Mundo |   Brasil |   Argentina |   total |
|:-----------------|--------:|---------:|------------:|--------:|
| Bancos           |     0.2 |    -10   |       -35.7 |   -45.6 |
| Energía          |     6.2 |     -6.6 |       -20.1 |   -20.6 |
| Servicios        |     1.2 |     -7.4 |       -31   |   -37.2 |
| Agro e inmuebles |    -0.5 |     -8.2 |        -1.3 |   -10   |

## Bonos soberanos (puntos log)

|       |   SPY |   BZ=F |   ^TNX |   Brasil |   idiosincrático |   total |
|:------|------:|-------:|-------:|---------:|-----------------:|--------:|
| Bonos |   0.2 |   -1   |   -0.7 |     -1.2 |             -8.7 |   -11.4 |
| GD30D |   0.2 |   -0.5 |   -0.2 |     -1.1 |             -2.6 |    -4.3 |
| GD35D |   0.3 |   -1   |   -1   |     -1.3 |            -12.1 |   -15   |
| GD41D |   0.3 |   -1.7 |   -0.9 |     -1.2 |            -11.2 |   -14.8 |

## Placebo: el mismo método en otros países (puntos log)

|                   |   Mundo |   Brasil |   Propio |   total |   beta Brasil |   R² |
|:------------------|--------:|---------:|---------:|--------:|--------------:|-----:|
| Argentina (ADRs)  |    2.03 |    -8.16 |   -22.24 |  -28.38 |          0.58 | 0.34 |
| Argentina (bonos) |   -1.49 |    -1.2  |    -8.66 |  -11.35 |          0.09 | 0.38 |
| México            |   -2.56 |    -5.4  |     6.81 |   -1.16 |          0.39 | 0.51 |
| Chile             |   -4.76 |    -6.65 |    -2.75 |  -14.15 |          0.48 | 0.59 |
| Perú              |   -3.28 |    -7.55 |     2.95 |   -7.89 |          0.54 | 0.53 |
| Colombia          |   -0.93 |    -5.4  |    12.81 |    6.48 |          0.39 | 0.29 |
| Emergentes        |   -2    |    -2.91 |    -2.4  |   -7.31 |          0.21 | 0.67 |

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

Correlación beta vs caída (ADRs argentinos, n=13): -0.68, p = 0.011.

Traspaso: caída real / caída predicha por el beta a Brasil (log, promedio por grupo).

| grupo     |   pred |   real |   traspaso |
|:----------|-------:|-------:|-----------:|
| Argentina | -0.15  | -0.057 |      0.378 |
| Brasil    | -0.214 | -0.188 |      0.878 |
| MELI      | -0.076 | -0.081 |      1.068 |

## ¿Los días grandes de Brasil traspasan menos?

Regresión de AR sobre mundo + Brasil + Brasil x (|shock| > 2.5 desvíos), toda la muestra sin el 26-27/10/2026.

|                     |   beta |     t |
|:--------------------|-------:|------:|
| Brasil              |   0.59 |  9.64 |
| Brasil x día grande |  -0.12 | -1.18 |

Por umbral:

|             |   días grandes |   beta normal |   diferencia |     t |
|:------------|---------------:|--------------:|-------------:|------:|
| 2.0 desvíos |             61 |          0.58 |        -0.07 | -0.68 |
| 2.5 desvíos |             30 |          0.59 |        -0.12 | -1.18 |
| 3.0 desvíos |             14 |          0.58 |        -0.11 | -0.96 |

Traspaso por tamaño del shock (pendiente sin constante):

|       |   días |   traspaso |    ee |
|:------|-------:|-----------:|------:|
| < 1   |    789 |      0.613 | 0.128 |
| 1 a 2 |    256 |      0.515 | 0.066 |
| 2 a 3 |     47 |      0.532 | 0.081 |
| > 3   |     14 |      0.436 | 0.071 |

Los 10 días con mayor shock propio de Brasil (log):

| Date                | Brasil   | Argentina   |   traspaso |
|:--------------------|:---------|:------------|-----------:|
| 2022-10-03 00:00:00 | +6.3%    | +2.0%       |       0.32 |
| 2022-10-24 00:00:00 | -7.5%    | -2.4%       |       0.31 |
| 2022-10-31 00:00:00 | +4.7%    | +2.1%       |       0.45 |
| 2022-11-07 00:00:00 | -5.3%    | -3.7%       |       0.69 |
| 2022-11-10 00:00:00 | -13.1%   | -7.6%       |       0.58 |
| 2023-01-03 00:00:00 | -7.9%    | -1.3%       |       0.16 |
| 2023-04-11 00:00:00 | +5.2%    | +2.6%       |       0.51 |
| 2025-12-05 00:00:00 | -6.6%    | -2.2%       |       0.34 |
| 2026-10-05 00:00:00 | +11.2%   | +5.1%       |       0.46 |
| 2026-10-26 00:00:00 | -22.8%   | -6.4%       |       0.28 |

Beta rodante a Brasil: promedio 2025 0.41, septiembre 2026 0.80, último 0.44.
