$('#id_company, #id_customer, #id_credit_type, #id_unit_type, #id_status, #id_product').select2({
    width: "100%",
});

var data_company_customers = null
var data_company_products = null
var selected_customer = $('#id_customer').find('option:selected').val();
$("#form_credit_memo #id_customer").empty()
$("#form_credit_memo #id_product").empty()
var added_product_ids = [];

if (company_admin_company_id) {
    ajax_call_get_customers_and_products(company_admin_company_id);
} else {
    selected_company = $('#id_company').find('option:selected').val();
    ajax_call_get_customers_and_products(selected_company);


    // $("#id_company").on('change', function() {
    //     reset_form_on_product_company_change();
    //     $this = $(this);
    //     company_id = $this.val();
    //     if (company_id != '') {
    //         ajax_call_get_customers_and_products(company_id);
    //     }
    // });
}
// $("#id_customer").select2("val", selected_customer);
// $("#id_customer").val(selected_customer).trigger('change');
// $("#id_customer").val(selected_customer).change();
// $("#id_customer option[value=" + selected_customer + "]").attr('selected', 'selected');
// $("#id_customer").select2().trigger('change');

ajax_call_credit_memo_product_in_update(credit_memo_id);

// if (update_form) {
//     selected_vendor = $('#id_vendor').find('option:selected').val();
//     $("#form_credit_memo #id_vendor").empty().append("<option value=''>---------</option>");
//     $("#form_credit_memo #id_product").empty().append("<option value=''>---------</option>");
//     if (company_admin_company_id) {
//         ajax_call_get_customers_and_products(company_admin_company_id);
//     } else {
//         selected_company = $('#id_company').find('option:selected').val();
//         ajax_call_get_customers_and_products(selected_company);


//         $("#id_company").on('change', function() {
//             reset_credit_memo_form_on_product_company_change();
//             $this = $(this);
//             company_id = $this.val();
//             if (company_id != '') {
//                 ajax_call_get_customers_and_products(company_id);
//             }
//         });
//     }
//     ajax_call_purchase_order_product_in_update(purchase_order_id);


// } else {

//     $("#form_credit_memo #id_vendor").empty().append("<option value=''>---------</option>");
//     $("#form_credit_memo #id_product").empty().append("<option value=''>---------</option>");
//     if (company_admin_company_id) {
//         ajax_call_get_customers_and_products(company_admin_company_id);
//     } else {
//         $("#id_company").on('change', function() {
//             reset_credit_memo_form_on_product_company_change();
//             $this = $(this);
//             company_id = $this.val();
//             if (company_id != '') {
//                 ajax_call_get_customers_and_products(company_id);
//             }
//         });
//     }


// }



$(document).on("change", "#id_company", function() {
    //reset_credit_memo_form_on_product_company_change();
    $this = $(this);
    company_id = $this.val();
    if (company_id != '') {
        ajax_call_get_customers_and_products(company_id);
    }
});

function ajax_call_get_customers_and_products(company_id) {
    $.ajax({
        url: data_url,
        type: "GET",
        dataType: "json",
        data: {
            'company_id': company_id
        },
        success: function(data) {
            $("#form_credit_memo #id_customer").empty().append("<option value=''>---------</option>");
            $("#form_credit_memo #id_product").empty().append("<option value=''>---------</option>");
            data_company_customers = data.company_customers;
            data_company_products = data.company_products;
            $("#form_credit_memo #id_customer").append(data_company_customers);
            $("#form_credit_memo #id_product").append(data_company_products);
            // $("#id_customer").select2("val", selected_customer);
            // $("#id_customer").val(selected_customer).trigger('change');
            // $("#id_customer").val(selected_customer).change();
            $("#id_customer option[value=" + selected_customer + "]").attr('selected', 'selected');
            $("#id_customer").select2().trigger('change');
            // $("#id_customer").select2().trigger('change');
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}

$(document).on("change ", "#id_product ", function() {
    product = $(this);
    if (product.val() != '') {
        ajax_call_get_product_details(product)
        $("#btn_add_product").removeClass("btn-pointer-events-none");
    } else {
        // $("#btn_add_product").addClass("btn-pointer-events-none");
        reset_add_product_fields();
    }
});

function ajax_call_get_product_details(product) {
    $.ajax({
        url: product.attr("data-url"),
        type: "GET",
        dataType: "json",
        data: {
            'product_id': product.val(),
        },
        success: function(data) {
            product_single_piece_price = parseFloat(data.product_cost_price)
            $("#form_credit_memo #id_unit_type").empty();
            $("#form_credit_memo #id_unit_type").append(data.product_unit_type);
            $("#form_credit_memo #id_return_quantity").val("1");
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}

$(document).on("click", "#btn_add_product", function() {
    if ($('#id_product').val() != '') {
        ajax_call_add_product_in_credit_memo_list($(this));
    }
});

function ajax_call_add_product_in_credit_memo_list($this) {
    selected_product_id = $('#id_product').val();
    $.ajax({
        url: $this.attr("data-url"),
        type: "post",
        dataType: "json",
        data: {
            'product_id': selected_product_id,
            'unit_type': $('#id_unit_type').find('option:selected').attr('data-product-type'),
            'unit_type_text': $('#id_unit_type').find('option:selected').text(),
            'unit_type_pieces': $('#id_unit_type').val(),
            'quantity': $('#id_return_quantity').val(),
        },
        headers: { "X-CSRFToken": $("#form_credit_memo input[name='csrfmiddlewaretoken']").val() },
        success: function(data) {
            if ($('#table_added_products').has('.no-product-row').length > 0) {
                $('.no-product-row').remove();
            }
            $('#table_added_products').append(data.product_row);
            added_product_ids.push(selected_product_id);
            $("#form_credit_memo #product_id_list ").val(added_product_ids);

            calculate_credit_memo_total();
            count_credit_memo_table_row_index();
            reset_credit_memo_add_product_fields();
            remove_credit_memo_product_from_selection(added_product_ids);

        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}

function count_credit_memo_table_row_index() {
    index = 1;
    $(".product-row").each(function() {
        $(this).find("td[data-title='product-id']").text(index);
        index += 1;
    });
}

function reset_credit_memo_add_product_fields() {
    // $("#form_credit_memo #id_vendor").empty().append("<option value=''>---------</option>");
    $("#form_credit_memo #id_product").empty().append("<option value=''>---------</option>");
    $("#form_credit_memo #id_unit_type").empty().append("<option value=''>---------</option>");
    // $("#form_credit_memo #id_vendor").append(data_company_vendors);
    $("#form_credit_memo #id_product").append(data_company_products);
    $("#form_credit_memo #id_return_quantity").val("0");
    $("#form_credit_memo #id_total_pieces").val("0");
    $("#btn_add_product").addClass("btn-pointer-events-none");

}

function remove_credit_memo_product_from_selection(id_array) {
    id_array.forEach(function(value, index, array) {
        $("#id_product option[value='" + value + "']").remove();
    });
}

$(document).on("click", ".btn-product-remove", function() {
    product_id_removed_from_added_list = $(this).closest('tr').attr('product-id');
    id_index = added_product_ids.indexOf(product_id_removed_from_added_list);
    if (id_index > -1) {
        added_product_ids.splice(id_index, 1);
    }
    $("#form_credit_memo #product_id_list ").val(added_product_ids);

    reset_credit_memo_add_product_fields();
    remove_credit_memo_product_from_selection(added_product_ids);

    $(this).closest('tr').remove();
    count_credit_memo_table_row_index();

    calculate_credit_memo_total();
});

function calculate_credit_memo_total() {
    credit_memo_sum = 0;
    product_prices = [];
    $(".product-total-price").each(function() {
        product_prices.push(parseFloat($(this).val()));
    });
    credit_memo_sum = product_prices.reduce((sum, a) => sum + a, 0);
    $("#form_credit_memo #id_item_total ").val(credit_memo_sum.toFixed(2));
    //$("#form_credit_memo #id_grand_total ").val(credit_memo_sum.toFixed(2));
    calculate_grand_total()

}
$(document).on("change", "#id_discount", function() {
    calculate_grand_total()
})

$(document).on("change", "#discount_amount", function() {
    discount = $("#discount_amount").val();
    item_total = $("#form_credit_memo #id_item_total").val();
    grand_total = parseFloat(item_total) - discount
    floor_val = Math.floor(grand_total)
    floor_remaining = grand_total - floor_val
    if (floor_remaining >= 0.5) {
        floor_val += 1
        adjustment = 1 - floor_remaining
    } else {
        adjustment = 0 - floor_remaining
    }
    discount_amount = (item_total - grand_total) / item_total * 100
    $("#form_credit_memo #id_discount").val(discount_amount.toFixed(2))
    $("#form_credit_memo #id_adjustment").val(adjustment.toFixed(2))
    $("#form_credit_memo #id_grand_total ").val(floor_val.toFixed(2))
})

function calculate_grand_total() {
    discount = $("#id_discount").val();
    item_total = $("#form_credit_memo #id_item_total").val();
    grand_total = parseFloat(item_total) - parseFloat(parseFloat(item_total) / 100) * discount
    floor_val = Math.floor(grand_total)
    floor_remaining = grand_total - floor_val
    if (floor_remaining >= 0.5) {
        floor_val += 1
        adjustment = 1 - floor_remaining
    } else {
        adjustment = 0 - floor_remaining
    }
    discount_amount = item_total - grand_total
    $("#form_credit_memo #discount_amount").val(discount_amount.toFixed(2))
    $("#form_credit_memo #id_adjustment").val(adjustment.toFixed(2))
    $("#form_credit_memo #id_grand_total ").val(floor_val.toFixed(2))
}


function make_input_name($id, $field) {
    return "input[name=" + $id + $field + "]";
}

function calculate_credit_memo_product_net_price($this) {
    $row_id = $this.attr("data-id");
    $prd_quantity = parseInt($this.find(make_input_name($row_id, "__quantity")).val());
    $prd_default_total_pieces = parseInt($this.find(make_input_name($row_id, "__totalpieces")).attr("data-default-value"));
    // console.log("prd_default_total_pieces " + $prd_default_total_pieces);
    $prd_total_pieces = parseInt($this.find(make_input_name($row_id, "__totalpieces")).val());
    $prd_unit_price = parseFloat($this.find(make_input_name($row_id, "__unitprice")).val());

    $prd_total_pieces = $prd_default_total_pieces * $prd_quantity

    $prd_item_total_price = $prd_total_pieces * $prd_unit_price;

    $this.find(make_input_name($row_id, "__quantity")).val($prd_quantity);
    $this.find(make_input_name($row_id, "__unitprice")).val($prd_unit_price.toFixed(2));
    $this.find(make_input_name($row_id, "__totalprice")).val($prd_item_total_price.toFixed(2));
    calculate_credit_memo_total();

}


$(document).on('click focusout', "#table_added_products .product-row", function(e) {
    if (e.target) {
        if ($(e.target).hasClass('btn-procuct-remove')) {
            product_id_removed_from_added_list = $(e.target).closest('tr').attr('product-id');
            id_index = added_product_ids.indexOf(product_id_removed_from_added_list);
            if (id_index > -1) {
                added_product_ids.splice(id_index, 1);
            }
            $("#form_credit_memo #product_id_list ").val(added_product_ids);

            reset_credit_memo_add_product_fields();
            remove_credit_memo_product_from_selection(added_product_ids);

            $(e.target).closest('tr').remove();
            count_table_row_index_credit_memo();

            calculate_credit_memo_total();
        } else {
            if (e.key !== ".") {
                calculate_credit_memo_product_net_price($(e.target).closest("tr"));
            }
        }
    }
});

function reset_credit_memo_form_on_product_company_change() {
    reset_credit_memo_add_product_fields();
    $("#table_added_products .product-row").remove();
    if ($('#table_added_products').has('.no-product-row').length == 0) {
        $("#table_added_products tbody").append("<tr class='no-product-row'><td colspan='8'><p>No products added</p></td> </tr>");
    }

}

function count_table_row_index_credit_memo() {
    indx = 1;
    $(".product-row").each(function() {
        $(this).find("td[data-title='product-id']").text(indx);
        indx += 1;
    });
}
$(document).on("change", ".damage-quantity, .fresh-quantity", function() {
    product_id = $(this).data("product-id")
    fresh_qty = $("#fresh-return-quantity-" + product_id).val()
    damage_qty = $("#damage-return-quantity-" + product_id).val()
    total_qty = parseInt(fresh_qty) + parseInt(damage_qty)
    return_qty = $("#return-quantity-" + product_id).val(total_qty)
})
$(document).on("change", ".return-quantity", function() {
    product_id = $(this).data("product-id")
    return_qty = $("#return-quantity-" + product_id).val()
    fresh_qty = $("#fresh-return-quantity-" + product_id).val(return_qty)
    damage_qty = $("#damage-return-quantity-" + product_id).val("0")
        // total_qty = parseInt(return_qty) - parseInt(damage_qty)
        // $("#fresh-return-quantity-" + product_id).val(total_qty)
})

function ajax_call_credit_memo_product_in_update(credit_memo_id) {

    $.ajax({
        url: update_credit_memo_url,
        type: 'GET',
        dataType: "json",
        data: {
            'credit_memo_id': credit_memo_id,
        },
        success: function(data) {
            if ($('#table_added_products').has('.no-product-row').length > 0) {
                $('.no-product-row').remove();
            }
            $('#table_added_products').append(data.existing_product_list);
            $("#form_credit_memo #product_id_list ").val(data.credit_memo__product_ids);
            added_product_ids = data.credit_memo__product_ids.map(String);
            remove_credit_memo_product_from_selection(added_product_ids);

            // calculate_purchase_order_total();
            // count_table_row_index();
            // reset_add_product_fields();
            // remove_product_from_selection(added_product_ids);

        }

    })
}