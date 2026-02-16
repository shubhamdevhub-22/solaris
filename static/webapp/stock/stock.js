function reset_form(){
    $('#id_product').val("").change();
    $('#id_warehouse').val("").change();
    $('#id_vehicle').val("").change();
    $('#id_barcode').val("");
    $('#id_available_stock').val(0);
}

function validateForm(id){
    var has_error = false;
    var inputs;

    if(!id.includes("update")){
        inputs = $(document).find(`${id} input, ${id} select`);
    }
    else {
        inputs = $(document).find(`${id} select`);
    }

    inputs.each(function(index) {
        if(!$(this).is(":hidden")){
            if($(this).val() == null || $(this).val() == "" || $(this).val() == "0"){
                const name = $(this).attr("name").replaceAll("_", " ");
                if (!$(this).hasClass("select2-list")){
                    if ($(this).siblings().length <= 0){
                        $(this).parent().append(`<span class='text-danger'>Please enter ${name}</span>`);
                    }
                }
                else {
                    if ($(this).siblings().length <= 1){
                        $(this).parent().append(`<span class='text-danger'>Please select ${name}</span>`);
                    }
                }
                has_error = true;
            } else {
                if (!$(this).hasClass("select2-list")){
                    $(this).siblings().remove();
                }
                else {
                    if ($(this).siblings().length >= 2){
                        $(this).siblings(":last").remove();
                    }
                }
            }
        }
    })
    return has_error;
}

$(document).ready(function(){

    $(document).on("click", ".stock-update", function(){
        const id = $(this).data("id");
        $(`#id_stock-${id}`).removeAttr("disabled");
        $(this).parent().children(':first-child').focus();
    });

    $(document).on("input", ".update-ready-stock", function(){
        const max = $(this).data("max");
        const value = $(this).val();

        if(value > max){
            $(this).val(max);
        }

        if(value < 0){
            $(this).val(0);
        }
    });

    $(document).on("click", "#add_stock_btn", function(e){
        e.preventDefault();

        if(validateForm("#addStockModal")) {
            return false;
        }

        var data = {"csrfmiddlewaretoken": csrf_token, "stock_type": "add"};

        var product = $(document).find('#addStockModal #id_modal_product').val()
        if (product){
            data["product"] = product
        }

        var warehouse = $(document).find('#addStockModal #id_modal_warehouse').val()
        if (warehouse){
            data["warehouse"] = warehouse
        }

        var stock = $(document).find('#addStockModal #id_stock').val()
        if (stock){
            data["stock"] = stock
        }

        $.ajax({
            url: stock_url,
            type: 'post',
            data : data,
            success: function (data){
                if (data["message"]) {
                    $("#add_stock_modal").html("");
                    $("#addStockModal").modal("hide");
                    $("#id_product").select2().val(product).trigger("change");
                    $("#id_warehouse").select2().val(warehouse).trigger("change");
                    $("#id_available_stock").val(data.stock);
                    $("#id_barcode").val("");
    
                    $.toast({
                        text: data.message,
                        position: 'bottom-right',
                        stack: false,
                        icon: 'success',
                    })
                }
                if (data["error"]){
                    $.toast({
                        text: data.error,
                        position: 'bottom-right',
                        stack: false,
                        icon: 'error',                    
                    })
                }
                   
            }
        })

    })

    $(document).on("click", "#update_stock_btn", function(e){
        e.preventDefault();

        if(validateForm("#updateStockModal")) {
            return false;
        }

        var data = {"csrfmiddlewaretoken": csrf_token, "stock_type": "update"};

        var product = $(document).find('#updateStockModal #id_modal_product').val()
        if (product){
            data["product"] = product
        }

        var warehouse = $(document).find('#updateStockModal #id_modal_warehouse').val()
        if (warehouse){
            data["warehouse"] = warehouse
        }

        var stock = $(document).find('#updateStockModal #id_stock').val()
        if (stock){
            data["stock"] = stock
        }

        if(parseInt(data["stock"]) == parseInt($('#id_available_stock').val())){
            return;
        }

        $.ajax({
            url: stock_url,
            type: 'post',
            data : data,
            success: function (data){
                if (data["message"]) {
                    $("#update_stock_modal").html("");
                    $("#updateStockModal").modal("hide");
                    
                    $("#id_product").val(product).trigger("change");
                    $("#id_warehouse").val(warehouse).trigger("change");

                    $("#id_available_stock").val(data.stock);
                    $("#id_barcode").val("");
    
                    $.toast({
                        text: data.message,
                        position: 'bottom-right',
                        stack: false,
                        icon: 'success',
                    })
                }
                if (data["error"]){
                    $.toast({
                        text: data.error,
                        position: 'bottom-right',
                        stack: false,
                        icon: 'error',                    
                    })
                }
                   
            }
        })

    })

    $(document).on("click", "#id_add_stock_button", function(e){
        
        $.ajax({
            url: stock_form_url,
            type: 'get',
            data : {
                'product':$('#id_product').val(),
                'warehouse':$('#id_warehouse').val(),
                'vehicle':$('#id_vehicle').val(),
                //"csrfmiddlewaretoken": csrf_token,
            },
            success: function (data){
                $("#addStockModal").modal("show");
                $("#add_stock_modal").html(data.html);

                $("#add_stock_modal #id_modal_warehouse").select2({
                    width: "100%",
                });

                $("#add_stock_modal #id_modal_product").select2({
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
            }
        })
        
    })

    $(document).on("click", "#id_update_stock_button", function(e){
        $.ajax({
            url: stock_form_url,
            type: 'get',
            data : {
                'product':$('#id_product').val(),
                'warehouse':$('#id_warehouse').val(),
                'vehicle':$('#id_vehicle').val(),
                'stock':$('#id_available_stock').val(),
                //"csrfmiddlewaretoken": csrf_token,
            },
            success: function (data){
                $("#updateStockModal").modal("show");
                $("#update_stock_modal").html(data.html);

                $("#update_stock_modal #id_modal_warehouse").select2({
                    width: "100%",
                });

                $("#update_stock_modal #id_modal_product").select2({
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
                }).on("change", function(e){
                    loadstockproductform(true);
                });
            }
        })
    })
})

function disableInput(el){
    $(el).attr('disabled', true);
    const id = $(el).data("id");
    
    const url = stock_update_url.replace("0", id);

    $.ajax({
        type: "POST",
        url: url,
        data: {
            "value": el.value,
            "csrfmiddlewaretoken": csrf_token,
        },
        success: function (data) {
            $("#table").DataTable().ajax.reload(null, false);

            $.toast({
                text: data.message,
                position: 'bottom-right',
                stack: false,
                icon: data.level,
            })
        }    
    });
}