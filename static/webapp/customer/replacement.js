var product_single_piece_price = 0;
var data_company_customers = null;
var data_company_warehouses = null;
var data_company_products = null;
var added_product_ids = [];
var selected_warehouse = null;
var selected_customer = null;
var exchange = false;
var textable = false;
var free_item = false;
var update_view_first_page_load = false;
const csrf_token = $("#replacement_form input[name='csrfmiddlewaretoken']").val();

function reset_order(is_order_change){
    if (is_order_change) {
        $("#id_order").val("").change();
    }
    $("#id_product").val("").change();
    $("#id_total_amount").val(0);
}

function reset_form_on_product_company_customer_change(is_order_change=true) {
    reset_order(is_order_change);

    added_product_ids = [];
    $("#product_id_list").val(added_product_ids);
    $("#table_added_products .product-row").remove();
    if ($('#table_added_products').has('.no-product-row').length == 0) {
        $("#table_added_products tbody").append("<tr class='no-product-row'><td colspan='12'><p>No products added</p></td> </tr>");
    }
}

$(document).ready(function() {
    if(company_admin_company_id == null){
        $("#id_company").select2({
            width: "100%",
        }); 
    }

    $("#id_return_type").select2({
        width: "100%",
    })

    $("#id_customer").select2({
        width: "100%",
        placeholder: "All",
        ajax: {
            url: customer_search_url,
            data: function (params) {
                var query = {
                    search: params.term,
                    type: 'public'
                }
                const id_company = $("#id_company").val();
                if (id_company){query["company"] = id_company;}
                return query;
            },
            processResults: function (data) {
                return {
                  results: data.items
                };
            },
        }
    }).on("select2:select", function(e){
        reset_form_on_product_company_customer_change();

        $("#id_customer_code").val(e.params.data.code);
        $("#id_zone").val(e.params.data.zone);
    });

    var previous_order_id = "";

    $(`#id_order`).select2({
        width: "100%",
        placeholder: "All",
        ajax: {
            url: order_search_url,
            data: function (params) {
                var query = {
                    search: params.term,
                    type: 'public'
                }
                const id_company = $("#id_company").val();
                if (id_company){query["company"] = id_company;}
                const id_customer = $("#id_customer").val();
                if (id_customer){query["customer"] = id_customer;}
                return query;
            },
            processResults: function (data) {
                return {
                  results: data.items
                };
            },
        }
    }).on("select2:select", function(e){
        const current_val = $(this).val();
        if(previous_order_id != current_val){
            reset_form_on_product_company_customer_change(false);
        }
        previous_order_id = current_val;
    });

    $(`#id_product`).select2({
        width: "100%",
        placeholder: "All",
        ajax: {
            url: product_search_url,
            data: function (params) {
                var query = {
                    search: params.term,
                    type: 'public'
                }
                query["added_product_list"] = JSON.stringify(added_product_ids);
                const id_company = $("#id_company").val();
                if (id_company){query["company"] = id_company;}
                const id_customer = $("#id_customer").val();
                if (id_customer){query["customer"] = id_customer;}
                const id_order = $("#id_order").val();
                if (id_order){query["order"] = id_order;}
                return query;
            },
            processResults: function (data) {
                return {
                  results: data.items
                };
            },
        }
    })

    $(document).on("keyup", ".replace-quantity", function() {
        const product_id = $(this).data("id");

        var qty = parseInt($(this).val());
        if(!qty){qty=0;}
        if(qty < 0){$(this).val(0); qty=0;}

        const avail_to_replace = parseInt($(document).find(`#id_product_${product_id}_available_replacement_quantity`).val());

        if(qty > avail_to_replace){
            $(this).val(avail_to_replace);
            qty = avail_to_replace;
        }

        const unit_price = parseFloat($(document).find(`#id_product_${product_id}_unitprice`).val());

        const item_total = unit_price * qty;
        $(document).find(`#id_product_${product_id}_replace_amount`).val(item_total.toFixed(2));

        calculate_order_total();
    });

    $(document).on("keyup", ".replace-amount", function() {
        calculate_order_total();
    });

    if(update_form){
        $.ajax({
            url: add_replacement_product_url,
            type: "post",
            dataType: "json",
            data: {
                'replacement_id': replacement_id,
                'csrfmiddlewaretoken': csrf_token,
            },
            success: function(data) {
                if ($('#table_added_products').has('.no-product-row').length > 0) {
                    $('.no-product-row').remove();
                }
                $('#table_added_products').append(data.product_list);

                $("#product_id_list").val(data.replace_products);
                added_product_ids = data.replace_products.map(String);

                count_table_row_index();
            },
            error: function(xhr, ajaxOptions, thrownError) {
                console.log(thrownError);
            }
        });
    }

});

function add_product(){
    var order_product_id = $("#id_product").val();
    var customer_id = $("#id_customer").val();
    var order_id = $("#id_order").val();
    
    if(!customer_id){
        $.toast({
            text: "Please select the customer !!!",
            position: "bottom-right",
            stack: false,
            icon: "error",
          });
        return;
    }

    if(!order_id){
        $.toast({
            text: "Please select the order !!!",
            position: "bottom-right",
            stack: false,
            icon: "error",
          });
        return;
    }

    if(!order_product_id){
        $.toast({
            text: "Please select the product !!!",
            position: "bottom-right",
            stack: false,
            icon: "error",
          });
        return;
    }

    add_product_in_order_list(order_product_id);
}

function add_product_in_order_list(order_product_id){
    $.ajax({
        url: add_replacement_product_url,
        type: "post",
        dataType: "json",
        data: {
            'order_product_id': order_product_id,
            'csrfmiddlewaretoken': csrf_token,
        },
        success: function(data) {
            if ($('#table_added_products').has('.no-product-row').length > 0) {
                $('.no-product-row').remove();
            }
            $('#table_added_products').append(data.product_row);
            added_product_ids.push(order_product_id);
            $("#product_id_list").val(added_product_ids);

            $("#id_product").val("").change();
            count_table_row_index();
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}

$(document).on('click', ".btn-product-remove", function(e) {
    const product_id_removed_from_added_list = $(e.target).closest('tr').attr('product-id');
    //console.log("product_id_removed_from_added_list: "+product_id_removed_from_added_list);
    var id_index = added_product_ids.indexOf(product_id_removed_from_added_list);
    if (id_index > -1) {
        added_product_ids.splice(id_index, 1);
    }
    $("#product_id_list").val(added_product_ids);

    $(e.target).closest('tr').remove();
    count_table_row_index();
    calculate_order_total();
});

function calculate_order_total() {
    order_sum = 0;
    product_replace_amount = [];
    $("#table_added_products .replace-amount").each(function() {
        product_replace_amount.push(parseFloat($(this).val()));
    });
    order_sum = product_replace_amount.reduce((sum, a) => sum + a, 0);
    $("#id_total_amount").val(order_sum.toFixed(2));
}

function count_table_row_index() {
    indx = 1;
    $(".product-row").each(function() {
        $(this).find("td[data-title='product-id']").text(indx);
        indx += 1;
    });
}

$("#replacement_form").on('submit', function() {
    var count_row = $('.product-row').length
    if (count_row < 1) {
        $.toast({
            text: "Add at least one product !!!",
            position: 'bottom-right',
            stack: false,
            icon: 'error',
        })
        return false
    } else {
        return true;
    }
});
