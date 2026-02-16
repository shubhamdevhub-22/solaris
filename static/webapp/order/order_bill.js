function get_bill_product_unit_types(product_id, customer_id, url, prd_barcode) {
    ajax_call_setup();

    $.ajax({
        url: url,
        type: "post",
        dataType: "json",
        data: {
            'product_id': product_id,
            'customer_id': customer_id,
            'prd_barcode': prd_barcode,
        },
        success: function(data) {
            $("#id_available_stock").text(data.stock);
            $("#id_quantity").attr("max", data.stock);
            $("#id_product_brand").val(data.brand_name);
            $("#id_product_code").val(data.code);
            $("#id_previous_price").val(data.previous_price);

            if(is_bill_create){
                $("#order_form #id_unit").val(data.unit);
                if(!is_product_update){
                    $("#order_form #id_price_choice").val(data.applied_price.toLowerCase()).trigger("change");
                    $("#order_form #id_mrp").val(data.base_price);
                    $("#id_brand_primary_discount").val(data.primary_discount);
                    $("#id_brand_secondary_discount").val(data.secondary_discount);
                    $("#id_discount_applied").text(data.applied_discount);

                    if(!data.applied_discount.includes("No")) {
                        $("#id_special_rate, #id_special_discount").attr("disabled", "true");
                    }
                }

                if(data.applied_price.toLowerCase() == "mrp") {
                    show_discounts();
                }
                else {
                    hide_discounts();
                }
            }
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}

function hide_discounts(){
    $(".discounts").val("0");

    $("#id_brand_primary_discount").parent().parent().addClass("d-none");
    $("#id_brand_secondary_discount").parent().parent().addClass("d-none");
    $("#id_special_rate").parent().parent().addClass("d-none");
    $("#id_special_discount").parent().parent().addClass("d-none");
}

function show_discounts(){
    $("#id_brand_primary_discount").parent().parent().removeClass("d-none");
    $("#id_brand_secondary_discount").parent().parent().removeClass("d-none");
    $("#id_special_rate").parent().parent().removeClass("d-none");
    $("#id_special_discount").parent().parent().removeClass("d-none");
}

$(document).ready(function(){
    $("#order_form #id_price_choice").select2({
        width: "100%",
    }).on('select2:select', function() {
        var price_type = $(this).val();
        var product_id = $("#order_form #id_product").val();

        if(price_type != "mrp"){
            hide_discounts();
        }
        else {
            show_discounts();
        }

        if (product_id != '') {
            url = $(this).attr("data-url");
            $.ajax({
                url: url,
                type: "get",
                dataType: "json",
                data: {
                    'product_id': product_id,
                    'price_type': price_type,
                },
                success: function(data) {
                    if(data.error){
                        $.toast({
                            text: data.error,
                            position: 'bottom-right',
                            stack: false,
                            icon: 'error',
                        });
                    }
                    else {
                        $("#order_form #id_mrp").val(data.amount);
                    }
                },
                error: function(xhr, ajaxOptions, thrownError) {
                    console.log(thrownError);
                }
            });
        }
    })
})

function add_product_in_bill_list(product_id, quantity, unit_price, add_product_url, special_rate, special_discount, primary_discount, secondary_discount, free_quantity, price_type) {
    ajax_call_setup();
    $.ajax({
        url: add_product_url,
        type: "post",
        dataType: "json",
        data: {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'special_rate': special_rate,
            'special_discount': special_discount,
            'primary_discount': primary_discount,
            'secondary_discount': secondary_discount,
            'is_bill_create': is_bill_create,
            'free_quantity': free_quantity,
            'price_type': price_type,
        },
        success: function(data) {
            if(is_product_update){
                $(`#table_added_products #row_${product_id}`).html($(data.product_row).children());
                is_product_update = false;
            }
            else {
                if ($('#table_added_products').has('.no-product-row').length > 0) {
                    $('.no-product-row').remove();
                }
                added_product_ids.push(product_id);
                $("#order_form #product_id_list").val(added_product_ids);
                $('#table_added_products').append(data.product_row);
            }
            calculate_order_total();
            reset_add_product_fields();

            $("#id_product_extra_fields").addClass("d-none");
            $("#id_product_add_button").removeClass("d-none");
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}

$("#id_brand_primary_discount, #id_brand_secondary_discount").on("input", function(){
    $("#id_discount_applied").text("");
    var primary = $("#id_brand_primary_discount").val();
    var secondary = $("#id_brand_secondary_discount").val();

    if(primary){
        primary = parseFloat(primary);
        if(primary>100){
            $("#id_brand_primary_discount").val(100);
        }
    }

    if(secondary){
        secondary = parseFloat(secondary);
        if(secondary>100){
            $("#id_brand_secondary_discount").val(100);
        }
    }

    if(primary && secondary) {
        primary = parseFloat(primary);
        secondary = parseFloat(secondary);

        if(primary>0 || secondary>0){
            $("#id_special_rate, #id_special_discount").attr("disabled", "true");
        }
        else {
            $("#id_special_rate, #id_special_discount").removeAttr("disabled");
        }
    }
    else {
        if(primary){
            primary = parseFloat(primary);
            if(primary>0) {
                $("#id_special_rate, #id_special_discount").attr("disabled", "true");
            }
            else {
                $("#id_special_rate, #id_special_discount").removeAttr("disabled");
            }
        }
        else if(secondary) {
            secondary = parseFloat(secondary);
            if(primary>0) {
                $("#id_special_rate, #id_special_discount").attr("disabled", "true");
            }
            else {
                $("#id_special_rate, #id_special_discount").removeAttr("disabled");
            }
        }
        else {
            $("#id_special_rate, #id_special_discount").removeAttr("disabled");
        }
    }
});