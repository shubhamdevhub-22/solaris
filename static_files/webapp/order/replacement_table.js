var replacement_columns = [
    { data: 'id', name: 'id' },
    { data: 'replacement_order__replace_id', name:'replacement_order__replace_id' },
    { data: 'order_product__product', name:'order_product__product' },
    { data: 'order_product__unit_price', render: function ( number ) {return number.toLocaleString('en-IN', {maximumFractionDigits: 2, style: 'currency', currency: 'INR'})}, name:'order_product__unit_price' },
    { data: 'replace_quantity', name:'replace_quantity' },
    { data: 'total_amount', render: function ( number ) {return number.toLocaleString('en-IN', {maximumFractionDigits: 2, style: 'currency', currency: 'INR'})}, name: 'total_amount' },
]

function replacement_initialize_datatable(){
    $('#id_replacement_table').DataTable({
        columnDefs: [{
            orderable: false,
            targets: [-1]
        },
        ],
        order: [[0, 'desc']],
        processing: true,
        language: {
          processing: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading...</span>'
        },
        serverSide: true,
        bInfo:false,
        bLengthChange:false,
        searching:false,
        ajax: {
            url: replacement_url,
            type: 'get',
            data: {}
        },
        columns: replacement_columns,
        rowCallback: function (nRow, aData, iDisplayIndex) {
          var oSettings = this.fnSettings ();
          $("td:first", nRow).html(oSettings._iDisplayStart+iDisplayIndex +1);
          return nRow;
        },
    });
  }