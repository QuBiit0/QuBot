# 🏎️ Performance & Scalability Baseline

> **Tipo**: `rule` | **Versión**: 3.6.0 | **Archivos**: `13-performance-baseline.md`

## 📌 Criterios de Rendimiento Base

Ningún pull request ni feature de LMAgent debe afectar la performance escalonada de los sistemas. Estas reglas gobiernan la optimización del código genérico.

### 1. Asincronía Inquebrantable
- **Python (AsyncIO / FastAPI)** y **Node.js (Event Loop)** sufren de inanición si se insertan operaciones síncronas de Entrada/Salida en su hilo principal.
- Nunca usar `fs.readFileSync()`, `requests.get()`, o drivers SQL bloqueadores dentro de peticiones HTTP en vuelo.
- Paralelizar llamadas independientes de red iterativas usando `asyncio.gather()` o `Promise.all()`.

### 2. Big-O Constraints (Complejidad Algorítmica)
- **Evita n^2**: Si procesas mil ítems y tienes ciclos `[for { for {} }]` anidados `O(n^2)`, tu API fallará gravemente bajo carga pesada.
- Refactoriza agrupaciones en memoria empleando Hashmaps/Diccionarios (`O(1)` accesos) antes de iterar para correlacionar tablas intermedias si no puedes usar un `JOIN` de Base de Datos.

### 3. Indexado de Bases de Datos y N+1
- Cuando uses ORMs (Prisma, SQLAlchemy, Django), debes observar rigurosamente las descargas conectadas (*Eager Loading* vs *Lazy Loading*).
- El problema *N+1 Query* ocurre cuando cargas 100 Posteos, y el ORM hace 100 consultas extras para traer al Author de cada uno. Usa siempre pre-fetching o selectinload.
- Aplica índices `CREATE INDEX` en la DB para columnas de filtro, sorting y FKs de alto tránsito.

### 4. Patrones de Caché (Redis / In-memory)
Para recursos intensivos (como lectura de dashboards analíticos o resolución pesada algorítmica):
1. Intenta `Cache-Aside`: Verifica en Redis, si no existe consulta la DB, guarda resultante en Redis y retorna.
2. Invalida correctamente: Toda escritura a la misma entidad DB DEBE invalidar o actualizar la key del Redis correspondiente evitando data sucia (Stale data).
