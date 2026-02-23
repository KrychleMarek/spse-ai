# 2025MP42 SPŠE AI Chatbot pro školu



## Jak zprovoznit

1. **Build image** (v home dir projektu)
    ``` 
    docker compose up --build -d
    ```
2. **Zobrazení stránky**

    ``` localhost ```


## Zadání projektu

[Odkaz na zadání](https://gitlab.spseplzen.cz/studentske-projekty/projekty-2025-2026/mtp2/spse-ai-chatbot-pro-skolu/-/blob/master/_projektov%C3%A9%20podklady/zadani_dlouhodoba_maturitni_prace_stejskalm.pdf)

## Řešitelský tým
- sindelaradam22
- stejskalmarek22

## Vedoucí
kaucky

## Oponent
anderle


## Fáze a plnění
## Termíny
| milník                                | termín              |
| :------------------------------------ | :------------------ |
| První setkání                         | **5.9.2025** |
| První milník                          | **3.10.2025**  |
| Setkání se zákazníkem - specifikace   | **10.10.-17.10.2025** |
| Prefinální produkt                    | **27.3.2026** |
| Prezentace veletrh                    | **20.4.-24.4.2026** |

[^1]: Změněno na základě požadavků

### Ganttův diagram postupu
```mermaid
gantt
    title Milníky projektu
    dateFormat  YYYY-MM-DD
    section Intro
    První setkání                  :a1, 2025-09-05, 1d
    section První milník
    Koncept, breakout              :a2, 2025-10-03, 1d
    section Setkání se zákazníkem
    Setkání se zákazníkem          :a3, 2025-10-10, 7d
    section Vytvořený produktu
    Prefinální                     :a4, 2026-03-27, 1d
    section Prezentace
    veletrh                        :a5, 2026-04-20, 5d