function loadWareHouse() {
    var id_company = document.getElementById('id_company');
    var id_warehouse = document.getElementById('id_warehouse');
    var id_product= document.getElementById('id_product');
    var id_vehicle= document.getElementById('id_vehicle');
    var ajax = new XMLHttpRequest();
    id_warehouse.innerHTML = '';
    id_product.innerHTML = '';
    ajax.onreadystatechange = function () {
        if (ajax.readyState === 4) {
        $("#id_warehouse").empty().append("<option value=''>---------</option>");
        //$("#id_product").empty().append("<option value=''>---------</option>");
        $("#id_vehicle").empty().append("<option value=''>---------</option>");
            var list = JSON.parse(ajax.responseText);
            list.warehouse_list.forEach(element => {
                var option = document.createElement("option");
                option.value = element.id;
                option.text = element.name;
                id_warehouse.options.add(option);
            });
            // list.products_list.forEach(element => {
            //     var option = document.createElement("option");
            //     option.value = element.id;
            //     option.text = element.name+" - "+element.vehicle;
            //     id_product.options.add(option);
            // });
            list.vehicle_list.forEach(element => {
                var option = document.createElement("option");
                option.value = element.id;
                option.text = element.name;
                id_vehicle.options.add(option);
            });
            loadstockproductform()
        }
    };
    ajax.open('get', 'load_warehouse?id_company=' + id_company.value, true);
    ajax.send();   

}

var current_stock;
function loadstockproductform(is_modal=false){
    let product, warehouse;

    if (is_modal != true) {
        product=$('#id_product').val();
        warehouse=$('#id_warehouse').val();
    } else {
        product=$(document).find('#update_stock_modal #id_modal_product').val();
        warehouse=$(document).find('#update_stock_modal #id_modal_warehouse').val();
    }

    if(!product){
        $("#id_vehicle").val("").change();
    }

    var url = 'get_form/';
    $.ajax({
        url: url,
        type: 'get',
        data : {
            'product':product,
            'warehouse':warehouse,
        },
        success: function (data){
            if(data.html){
                $("#table-body").html(data.html);
            }
            if(data.vehicle_id){
                $("#id_vehicle").val(data.vehicle_id).change();
            } else {
                $("#id_vehicle").val("").change();
            }

            $(document).find("#updateStockModal #id_stock").val(data.available_stock);
            $("#id_available_stock").val(data.available_stock);
            current_stock = parseInt(data.available_stock);
        }
    });
    
}

function ajax_call_setup() {
    $.ajaxSetup({
        headers: { "X-CSRFToken": csrf_token }
    });

}

var request;
$("#id_barcode").on('input', function() {
    if (request){
        request.abort();
    }
    ajax_call_get_product_for_order_by_barcode($(this));
});

function productFormat(product) {
    if (!product.id) return product.text;

    var $product = $(
        '<div class="dropdown-css">'+
            '<div class="d-flex justify-content-between">'+
                '<div class="">'+ product.text +'</div>'+
                '<div class="">' + product.vehicle + '</div>' +
            '</div>'+
            '<div class="d-flex justify-content-between">'+
                '<div class="">'+ product.brand +'</div>'+
                '<div class="">' + product.code + '</div>' +
            '</div>'+
        '</div>');
    return $product;
}

$(document).ready(function(){
    $("#id_product").select2({
        width: "100%",
        templateResult: productFormat,
        ajax: {
            url: product_search_url,
            data: function (params) {
                var query = {
                    search: params.term,
                    type: 'public',
                }
                query["company"] = $("#id_company").val();
                return query;
            },
            processResults: function (data) {
                return {
                  results: data.items
                };
            },
        }
    });

    $(document).on("keyup", "#updateStockModal #id_stock", function(){
        const stock = parseInt($(this).val());
        
        if(stock < 0){
            $(this).val(0);
        }
    });
})

function ajax_call_get_product_for_order_by_barcode($this) {
    //   console.log("FIRE X");
    barcode_number = $this.val();

    //   console.log("barcode_number "+barcode_number);
    ajax_call_setup();
    request = $.ajax({
        url: $this.attr("data-url"),
        type: 'post',
        dataType: "json",
        data: {
            'barcode_number': barcode_number,
            'company_id': company_admin_company_id,
        },
        success: function(data) {
            if (data.product_id){
                $("#id_product").val(data.product_id).change();
            } else {
                if($("#id_product").val()){
                    $("#id_product").val("").change();
                    $("#id_vehicle").val("").change();
                    $("#id_available_stock").val(0);
                }
            }
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });

}