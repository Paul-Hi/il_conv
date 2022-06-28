document.addEventListener('DOMContentLoaded', function () {

    const table = document.getElementById('log_table');
    let thead, tbody, headings, rows, target_container, draggables;

    const parsePageLists = function () {
        thead = table.querySelector('thead');
        tbody = table.querySelector('tbody');
        headings = [...thead.querySelectorAll('th')];
        rows = tbody.querySelectorAll('tr');
        target_container = thead.querySelector('tr');
        draggables = [...target_container.querySelectorAll('.draggable')];
    };

    parsePageLists();

    [].forEach.call(headings, function (header) {
        header.addEventListener('click', function () {
            sortTableByColumn(header);
            parsePageLists();
        });
    });

    const direction_cache = Array.from(headings).map(function (_) {
        return '';
    })

    const changeOrder = function (column_idx) {

        const current_direction = direction_cache[column_idx] || 'asc';

        direction_cache[column_idx] = (current_direction == 'asc') ? 'desc' : 'asc';

        headings.forEach(function (h) {
            h.classList.remove('asc');
            h.classList.remove('desc');
        });

        headings[column_idx].classList.add(current_direction);

        return (current_direction == 'asc') ? 1 : -1;
    }

    const unpack = function (column_idx, content) {

        const column_type = headings[column_idx].getAttribute('data-type');


        switch (column_type) {
            case 'int':
                if (content == '') return 0;
                return parseInt(content);
            case 'datetime':
            case 'string':
            default:
                return content;
        }

    }

    const sortTableByColumn = function (column) {

        column_idx = headings.indexOf(column)

        const sorted = Array.from(rows);

        const dir = changeOrder(column_idx);


        sorted.sort(function (row_a, row_b) {
            const cell_a = row_a.querySelectorAll('td')[column_idx].innerHTML;
            const cell_b = row_b.querySelectorAll('td')[column_idx].innerHTML;

            const value_a = unpack(column_idx, cell_a);
            const value_b = unpack(column_idx, cell_b);

            if (value_a > value_b) return 1 * dir;
            else if (value_a < value_b) return -1 * dir;
            else return 0;

        });

        [].forEach.call(rows, function (row) {
            tbody.removeChild(row);
        });

        sorted.forEach(function (row) {
            tbody.appendChild(row);
        });
    }

    // drag'n'drop

    let drag_item = null;
    let source_idx = -1;
    let target_idx = -1;

    const addEventListeners = function () {
        draggables.forEach(draggable => {
            draggable.addEventListener('dragstart', () => {
                draggable.classList.add('dragging');
                drag_item = draggable;
                source_idx = draggables.indexOf(drag_item);
                table.classList.add('blur');
            })
            draggable.addEventListener('dragend', () => {
                swapTableColumnData()
                draggable.classList.remove('dragging');
                table.classList.remove('blur');
                drag_item = null;
            })
        })
    }

    addEventListeners();

    const swapTableColumnData = function () {
        target_idx = draggables.indexOf(drag_item);

        const all_rows = Array.from(rows);

        all_rows.forEach(function (row) {
            const cells = row.querySelectorAll('td');
            const source_cell = cells[source_idx];
            const cell_after = cells[target_idx + (target_idx > source_idx ? 1 : 0)];
            if (cells.length - 1 == target_idx) {
                row.appendChild(source_cell);
            }
            else {
                row.insertBefore(source_cell, cell_after);
            }
        });

        [].forEach.call(rows, function (row) {
            tbody.removeChild(row);
        });

        all_rows.forEach(function (row) {
            tbody.appendChild(row);
        });
    }

    const getElementAfterDropPosition = function (target_container, x) {
        const others = [...target_container.querySelectorAll('.draggable:not(.dragging)')];

        return others.reduce((closest_after, other) => {
            const bb = other.getBoundingClientRect();
            const halfwidth = (bb.right - bb.left) * 0.5;
            const offset = x - (bb.left + halfwidth);
            if (offset < 0 && offset > closest_after.offset) {
                return { offset: offset, element: other };
            }
            else {
                return closest_after;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    target_container.addEventListener('dragover', event => {
        event.preventDefault();
        let item_after = getElementAfterDropPosition(target_container, event.clientX);

        if (item_after == null) {
            target_container.appendChild(drag_item);
        }
        else {
            target_container.insertBefore(drag_item, item_after);
        }
        parsePageLists();
    })

});
