# Guía de Generación de Documentos

## PDF con pdfmake

### Definición de Estilos
```javascript
const styles = {
  header: { fontSize: 18, bold: true },
  tableExample: { margin: [0, 5, 0, 15] }
};
```

### Tablas
Usa `widths: ['*', 'auto', 100]` para controlar columnas.

## DOCX con docx
- Usa `Paragraph` y `TextRun` para texto.
- `Table` para estructuras de datos.

## Excel con exceljs
- `worksheet.columns` para definir headers.
- `worksheet.addRow()` para datos.
