$(function (e) {
    'use strict';

    // basic datatable
    $('#datatable-basic').DataTable({
        language: {
            searchPlaceholder: 'Search...',
            sSearch: '',
        },
        // columnDefs: [
        //     { targets: 0, orderable: false } // Disable sorting for the first column (index 0)
        // ],
        "pageLength": 10,
        scrollX: true
    });
    // basic datatable
});