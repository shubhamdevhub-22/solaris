

replacement_columns = [
    { data: 'id', name: 'id' },
    { data: 'replace_id', name: 'replace_id' },
    { data: 'created_at', name: 'created_at' },
    { data: 'return_type', name: 'return_type' },
    { data: 'replacement_total', render: function ( number ) {return number.toLocaleString('en-IN', {maximumFractionDigits: 2, style: 'currency', currency: 'INR'})}, name: 'replacement_total' },
    { data: 'actions', name: 'actions' },
]

document.addEventListener('htmx:afterRequest', function(evt) {
    // Put the JS code that you want to run here
    function set_filters(){
        var data = {}
        data["id_customer"] = $("#id_customer").val()
        return data
      }
      function initialize_datatable(){
        $('#replacement_table').DataTable({
            columnDefs: [{
                orderable: false,
                targets: [-1]
            },
            {
                targets: "_all",
                className: "text-center",
            }
            /*{
              targets: [],
              visible: role // new variable true or false based on user role.
            }*/
            ],
            order: [[0, 'desc']],
            // Ajax for pagination
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
                data: set_filters()
            },
            columns: replacement_columns,
            rowCallback: function (nRow, aData, iDisplayIndex) {
              var oSettings = this.fnSettings ();
              $("td:first", nRow).html(oSettings._iDisplayStart+iDisplayIndex +1);
              return nRow;
            },
        });
      }
      initialize_datatable();
});



ledger_columns = [
  { data: 'id', name: 'id' },
  { data: 'bill_id', name: 'bill_id' },
  { data: 'bill_date', name: 'bill_date' },
  { data: 'bill_amount', render: function ( number ) {return number.toLocaleString('en-IN', {maximumFractionDigits: 2, style: 'currency', currency: 'INR'})}, name: 'bill_amount' },
  { data: 'paid_amount', render: function ( number ) {return number.toLocaleString('en-IN', {maximumFractionDigits: 2, style: 'currency', currency: 'INR'})}, name: 'paid_amount' },
  { data: 'due_amount', render: function ( number ) {return number.toLocaleString('en-IN', {maximumFractionDigits: 2, style: 'currency', currency: 'INR'})}, name: 'due_amount' },
]

document.addEventListener('htmx:afterRequest', function(evt) {
  // Put the JS code that you want to run here
  function set_filters(){
      var data = {}
      data["id_customer"] = $("#id_customer").val()
      return data
    }
    function initialize_datatable(){
      $('#ledger_table').DataTable({
          columnDefs: [{
              orderable: false,
              targets: [-1]
          },
          {
              targets: "_all",
              className: "text-center",
          }
          /*{
            targets: [],
            visible: role // new variable true or false based on user role.
          }*/
          ],
          order: [[0, 'desc']],
          // Ajax for pagination
          processing: true,
          language: {
            processing: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading...</span>'
          },
          serverSide: true,
          bInfo:false,
          bLengthChange:false,
          searching:false,
          ajax: {
              url: ledger_url,
              type: 'get',
              data: set_filters()
          },
          columns: ledger_columns,
          rowCallback: function (nRow, aData, iDisplayIndex) {
            var oSettings = this.fnSettings ();
            $("td:first", nRow).html(oSettings._iDisplayStart+iDisplayIndex +1);
            return nRow;
          },
      });
    }
    initialize_datatable();
});