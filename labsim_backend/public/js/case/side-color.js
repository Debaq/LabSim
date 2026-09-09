// Rojo OD / azul OI para el SVG que arma este JS (audiograma, logograma,
// timpanograma, previsualizaciones de ABR y EOA).
//
// El color no se escribe acá: sale de --color-od/--color-oi en case.css, que
// es la única definición para los tres lenguajes (ese CSS, el SVG de las
// leyendas que arma case_create.php, y esto). Antes era el mismo hex repetido
// 43 veces; cambiar la convención clínica obligaba a encontrarlas todas.
//
// Se resuelve a hex en cada llamada, y no una vez al cargar, porque el
// dibujo entra por setAttribute('stroke', color) -- un atributo de
// presentación no resuelve var(), así que hay que pasarle el valor ya
// calculado. Sin cachear queda correcto si algún día estos tokens cambian
// con el tema (el toggle de _layout.php reescribe data-theme en caliente).
// Son unas pocas lecturas por redibujo de un SVG chico; no se nota.
window.sideColor = function sideColor(side) {
    var prop = side === 'od' ? '--color-od' : '--color-oi';
    var val = getComputedStyle(document.documentElement).getPropertyValue(prop).trim();
    // Si el CSS no cargó, mejor un color visible que un stroke vacío.
    return val || (side === 'od' ? '#b33a3a' : '#2255aa');
};
