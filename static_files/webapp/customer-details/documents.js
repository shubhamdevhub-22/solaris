

document_columns = [
    { data: 'id', name: 'id' },
    { data: 'docuemnt_name', name: 'docuemnt_name' },
    { data: 'document', name: 'document' },
    { data: 'actions', name:'actions' },
]

document.addEventListener('htmx:afterRequest', function(evt) {
    // Put the JS code that you want to run here
    function set_filters(){
        var data = {}
        data["id_customer"] = $("#id_customer").val()
        return data
      }
      function initialize_datatable(){
        $('#document_table').DataTable({
            columnDefs: [{
                orderable: false,
                targets: [0,1,2,3]
            },
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
                url: document_url,
                type: 'get',
                data: set_filters()
            },
            columns: document_columns,
            rowCallback: function (nRow, aData, iDisplayIndex) {
              var oSettings = this.fnSettings ();
              $("td:first", nRow).html(oSettings._iDisplayStart+iDisplayIndex +1);
              return nRow;
            },
        });
      }
      initialize_datatable();
});


$(document).on('click', '.ajax-document-delete-btn' , function (e){
    var id = $(this).data("id")
    var name = $(this).data("title")
    if(name == "None"){
        name = ""
    }
    var url = $(this).data("url")
    console.log(url)
    var delete_ele = $(this)


    Swal.fire({
        html: `Are you sure you want to delete <b>${name}</b> ?`,
        icon: 'question',
        showCloseButton: true,
        showCancelButton: true,
        confirmButtonColor: "#7442DB",
    }).then((result) => {
        
        /* Read more about isConfirmed, isDenied below */
        if (result.isConfirmed) {
            $.ajax({
                type: "POST",
                url: url,
                data: {
                    "id": id,
                    "csrfmiddlewaretoken": csrfm ,
                },
                success: function (data) {
                    $('#document_table').DataTable().ajax.reload(null, false);
                  
                  if (data["message"]){
                      $.toast({
                          text: data.message,
                          position: 'bottom-right',
                          stack: false,
                          icon: 'success',                    
                        })
                    }
                }    
            });
        }
    })
})