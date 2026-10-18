// Текущий год в подвале страницы
const yearElement = document.getElementById("current-year");
if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}

// Быстрый фильтр таблицы сертификатов по введенному тексту
const filterInput = document.getElementById("certificate-filter");
if (filterInput) {
    const rows = document.querySelectorAll("[data-filter-row]");
    filterInput.addEventListener("input", () => {
        const query = filterInput.value.trim().toLowerCase();
        rows.forEach((row) => {
            const text = row.textContent.toLowerCase();
            row.hidden = query !== "" && !text.includes(query);
        });
    });
}
