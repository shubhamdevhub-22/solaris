function initialize_datatable() {

    var t = $('#table').DataTable({
        columnDefs: [{
                "targets": 0,
                "className": "text-center",
            },
            {
                targets: [-1],
                orderable: false,
            },
            {
                targets: [2],
                visible: role
            }
        ],
        order: [],

        processing: true,
        language: {
            processing: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading...</span>'
        },
        serverSide: true,
        ajax: {
            url: data_table_url,
            type: 'get',
            data: set_filters(),
        },
        columns: columns_dtl,
        rowCallback: function(nRow, aData, iDisplayIndex) {
            var oSettings = this.fnSettings();
            $("td:first", nRow).html(oSettings._iDisplayStart + iDisplayIndex + 1);
            return nRow;
        },
    });

}

initialize_datatable();