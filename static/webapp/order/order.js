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
var is_product_update = false;

function customerFormat(customer) {
    if (!customer.id) return customer.text;

    var $customer = $(
        '<div class="d-flex justify-content-between">'+
        '<div>'+
        '<div class="">'+ customer.text +'</div>'+
        '</div>'+
        '<div>'+
        '<div class="">' + customer.area + '</div>'+
        '</div>'+
        '</div>');
    return $customer;
}

function productFormat(product) {
    if (!product.id) return product.text;

    var $product = $(
        '<div class="">'+
            '<div class="row">'+
                '<div class="col-5">'+ product.text +'</div>'+
                '<div class="col-3">'+ product.brand +'</div>'+
                '<div class="col-2 text-end">' + product.code + '</div>' +
                '<div class="col-2 text-end">' + product.vehicle + '</div>' +
            '</div>'+
            // '<div class="d-flex justify-content-between">'+
            // '</div>'+
        '</div>');
    return $product;
}

$(document).ready(function() {

    $(document).on("click", "#id_same_as_billing_address", function(){
        var value = $(this).prop("checked");
    
        if(value){
          $("#id_shipping_address_line_1").val($("#id_billing_address_line_1").val());
          $("#id_shipping_address_line_2").val($("#id_billing_address_line_2").val());
          $("#id_shipping_suite_apartment").val($("#id_billing_suite_apartment").val());
          $("#id_shipping_city").val($("#id_billing_city").val());
          $("#id_shipping_state").val($("#id_billing_state").val());
          $("#id_shipping_zip_code").val($("#id_billing_zip_code").val());
        }
        else {
          $("#id_shipping_address_line_1").val("");
          $("#id_shipping_address_line_2").val("");
          $("#id_shipping_suite_apartment").val("");
          $("#id_shipping_city").val("");
          $("#id_shipping_state").val("");
          $("#id_shipping_zip_code").val("");
        }
    });

    $(document).on("input", "#id_free_quantity", function(){
        var free_qty = $(this).val();
        if(!free_qty){free_qty=0;}
        var qty = $("#id_quantity").val();
        if(!qty){qty=0;}

        if(parseInt(free_qty) < 0){
            $(this).val(0);
        }

        if(parseInt(free_qty) > parseInt(qty)){
            $(this).val(qty);
        }
    })

    $("#id_warehouse, #id_product, #id_status").select2({
        width: "100%",
    });

    $("#id_customer").select2({
        width: "100%",
        templateResult: customerFormat,
        ajax: {
            url: customer_search_url,
            data: function (params) {
                var query = {
                    search: params.term,
                    type: 'public',
                    is_update: update_form,
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
    }).on("select2:select", function(e){
        if(is_bill_create){
            if(e.params.data.type == "retail") {
                $("#id_price_choice option").remove();
                $("#id_price_choice").append($("<option></option>").attr("value", "mrp").text("MRP"));
                $("#id_price_choice").append($("<option></option>").attr("value", "retail").text("Retail"));
            }
            else if(e.params.data.type == "wholesale") {
                $("#id_price_choice option").remove();
                $("#id_price_choice").append($("<option></option>").attr("value", "mrp").text("MRP"));
                $("#id_price_choice").append($("<option></option>").attr("value", "wholesale").text("Wholesale"));
            }
            else {
                $("#id_price_choice option").remove();
                $("#id_price_choice").append($("<option></option>").attr("value", "mrp").text("MRP"));
            }
        }
        reset_form_on_product_company_customer_change();
        $this = $(this);
        url = $this.attr("data-url");
        customer_id = $this.val();

        if (customer_id != '') {
            get_customer_details(customer_id, url);

        }

    });

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

    $("#id_special_rate").on("input", function(){
        var value = $(this).val();
        if(value) {
            value = parseFloat(value);
            if(value>0){
                $("#id_special_discount, #id_brand_primary_discount, #id_brand_secondary_discount").attr("disabled", "true");
            }
            else {
                $("#id_special_discount, #id_brand_primary_discount, #id_brand_secondary_discount").removeAttr("disabled", "true");
            }
        }
        else {
            $("#id_special_discount, #id_brand_primary_discount, #id_brand_secondary_discount").removeAttr("disabled", "true");
        }
    })

    $("#id_special_discount").on("input", function(){
        var value = $(this).val();
        if(value) {
            value = parseFloat(value);
            if(value>100){
                $(this).val(100);
            }
            
            if(value>0){
                $("#id_special_rate, #id_brand_primary_discount, #id_brand_secondary_discount").attr("disabled", "true");
            }
            else {
                $("#id_special_rate, #id_brand_primary_discount, #id_brand_secondary_discount").removeAttr("disabled");
            }
        }
        else {
            $("#id_special_rate, #id_brand_primary_discount, #id_brand_secondary_discount").removeAttr("disabled");
        }
    });

    if(company_admin_company_id == null){
        $("#id_company").select2({
            width: "100%",
        }); 
    }

    // $(document).find(`#order_form #id_brand`).select2({
    //     width: "100%",
    //     placeholder: "--------",
    //     ajax: {
    //         url: brand_search_url,
    //         data: function (params) {
    //             var query = {
    //                 search: params.term,
    //                 type: 'public'
    //             }
    //             query["company"] = $("#id_company").val();
    //             query["is_order"] = true;
    //             return query;
    //         },
    //         processResults: function (data) {
    //             return {
    //               results: data.items
    //             };
    //         },
    //     }
    // }).on("select2:select", function(e){
    //     reset_product_fields();

    //     if (company_admin_company_id) {
    //         ajax_call_setup();
    //         $.ajax({
    //             url: get_customers_products_url,
    //             type: "post",
    //             dataType: "json",
    //             data: {
    //                 'company_id': company_admin_company_id,
    //                 'brand': $(this).val(),
    //             },
    //             success: function(data) {
    //                 $("#order_form #id_product").empty().append("<option value=''>---------</option>");
    //                 $("#order_form #id_product").append(data.company_products);
    //             },
    //             error: function(xhr, ajaxOptions, thrownError) {
    //                 console.log(thrownError);
    //             }
    //         });
    //     }
    // });

    if (!update_form) {
        // $("#id_use_credits").attr("readonly", true);
        // $("#id_use_credits").val("0.00");

        $("#id_reference_number").attr("readonly", true);
        reset_form();
        if (!company_admin_company_id) {
            $("#order_form #id_company").on('change', function() {
                if (update_view_first_page_load == false) {
                    reset_form_on_product_company_customer_change();
                }
                // reset_form_on_product_company_customer_change();
                $this = $(this);
                company_id = $this.val();
                if (company_id != '') {
                    reset_form();
                    //get_customers(company_id);
                }
            });
        }
    } else {

        //update
        update_view_first_page_load = true;
        selected_customer = $('#id_customer').find('option:selected').val();
        reset_customer();
        reset_product();
        reset_unit_type();
        if (company_admin_company_id) {
            ajax_call_get_customers_and_warehouse_products(company_admin_company_id);
        } else {
            selected_company = $('#id_company').find('option:selected').val();
            ajax_call_get_customers_and_warehouse_products(selected_company);

            $("#id_company").on('change', function() {
                if (update_view_first_page_load == false) {
                    reset_form_on_product_company_customer_change();
                }
                $this = $(this);
                company_id = $this.val();
                if (company_id != '') {
                    ajax_call_get_customers_and_warehouse_products(company_id);
                }
            });
        }
        ajax_call_order_products_in_update(order_id);
        //calculate_overall_discount(parseFloat($("#id_customer_brand_discount").val()));
        calculate_adjustment_and_grand_total();
        calculate_balance_amount();
    }

    //common

    $(document).on("change", "#id_local_bill", function(){
        $(document).find("#local_bill_fields").toggleClass("d-none");
        if($(this).prop('checked') == true){
            $(document).find("#id_local_bill_value").val("true");
        }
        else {
            $(document).find("#id_local_bill_value").val("false");
        }
    });
    
    $("#order_form #id_product").on('change', function() {
        var product_id = $(this).val();
        var customer_id = $("#order_form #id_customer").val();
        
        reset_product_related_fields();
        
        if (product_id != '' && product_id != null) {
            $("#id_product_extra_fields").removeClass("d-none");
            $("#id_product_add_button").addClass("d-none");

            url = $(this).attr("data-url");
            if(is_bill_create){
                get_bill_product_unit_types(product_id, customer_id, url, null);
            }
            else {
                get_product_unit_types(product_id, url, no_reset = false, null);
            }
        }
    });

    // $("#order_form #id_unit_type").on('change', function() {
    //     if ($(this).val() != '') {
    //         $this = $(this);
    //         url = $this.attr("data-url");
    //         product_id = $("#id_product").val();
    //         customer_id = $("#id_product").attr("data-customer-id");
    //         unit_type = $this.val();
    //         if (product_id != '') {
    //             get_product_price_stock( product_id, customer_id, url, unit_type);
    //             reset_quantity();
    //         }
    //     }
    // });

    $("#order_form #id_quantity").on("keyup", function() {
        $("#btn_add_product").removeClass("btn-pointer-events-none");

        // var value = parseInt($(this).val());
        // var max_value = parseInt($(this).attr("max"));
        
        // if(value > max_value){
        //     $(this).val(max_value);
        // }
    });

    $("#product_radio_check .custom-control-input").on('change', function() {
        $("#product_radio_check .custom-control-input").not(this).prop('checked', false);
    });

    $("#order_form #btn_add_product").on('click', function() {
        var product_id = $("#order_form #id_product").val();
        var customer_id = $("#order_form #id_customer").val();
        
        if(!customer_id){
            $.toast({
                text: "Select the customer !!!",
                position: "bottom-right",
                stack: false,
                icon: "error",
              });
            $("#btn_add_product").addClass("btn-pointer-events-none");
            return;
        }

        if(!product_id){
            $.toast({
                text: "Select the product !!!",
                position: "bottom-right",
                stack: false,
                icon: "error",
              });
            $("#btn_add_product").addClass("btn-pointer-events-none");
            return;
        }

        id_qunatity = $("#order_form #id_quantity").val()
        if(parseInt(id_qunatity)>0){ 
            var add_product_url = $(this).attr("data-url");
            var quantity = $("#order_form #id_quantity").val();
            var unit_price = $("#order_form #id_mrp").val();

            var special_rate = $("#order_form #id_special_rate").val();
            if(!special_rate){special_rate=0;}
            var special_discount = $("#id_special_discount").val();
            if(!special_discount){special_discount=0;}
            var free_quantity = $("#id_free_quantity").val();
            if(!free_quantity){free_quantity=0;}
            
            
            if (product_id != '' & quantity != '') {

                if(is_bill_create){
                    var primary_discount = 0;
                    var secondary_discount = 0;
                    var price_type = $("#id_price_choice").val();

                    if(price_type == "mrp") {
                        primary_discount = $("#order_form #id_brand_primary_discount").val();
                        if(!primary_discount){primary_discount=0;}

                        secondary_discount = $("#order_form #id_brand_secondary_discount").val();
                        if(!secondary_discount){secondary_discount=0;}
                    }

                    reset_product_fields();
                    add_product_in_bill_list(product_id, quantity, unit_price, add_product_url, special_rate, special_discount, primary_discount, secondary_discount, free_quantity, price_type);
                }
                else{
                    reset_product_fields();
                    add_product_in_order_list(product_id, quantity, unit_price, add_product_url, special_rate, special_discount, free_quantity, price_type="mrp");
                }
            }
        } else {
            $.toast({
                text: "Add Valid Product Quantity",
                position: "bottom-right",
                stack: false,
                icon: "error",
              });
            $("#btn_add_product").addClass("btn-pointer-events-none");
        }
    });

    // <-------- CREATE ORDER ------------------->

    $("#id_barcode").on('change', function() {
        if ($(this).val() != '') {
            reset_brand();
            ajax_call_get_product_for_order_by_barcode($(this));
        }
    });

    // <-------- END OF CREATE ORDER ------------------->



    $(document).on("input", "#generate_bill_modal #id_shipping_charges", function() {
        
        // shipping_charges = parseFloat($("#id_shipping_charges").val());
        // console.log('shipping_charges:', shipping_charges)
        // grandtotal = parseFloat($("#id_grand_total").val());
        // console.log('grandtotal:', grandtotal)
        // new_grand_total = grandtotal + shipping_charges
        // console.log('new_grand_total:', new_grand_total)
        // $("#id_grand_total").val(new_grand_total);
        calculate_adjustment_and_grand_total();

    });
    
    $(document).on("input", "#generate_bill_modal #id_packing_charges", function() {
        
        // packing_charges = parseFloat($("#id_packing_charges").val());
        // console.log('packing_charges:', packing_charges)
        // grandtotal = parseFloat($("#id_grand_total").val());
        // console.log('grandtotal:', grandtotal)
        // new_grand_total = grandtotal + packing_charges
        // console.log('new_grand_total:', new_grand_total)
        // $("#id_grand_total").val(new_grand_total);
        calculate_adjustment_and_grand_total();
    });


    // $("#order_form #id_use_credits").on("mouseup focusout change", function () {
    //   $(this).val(Math.min($(this).attr("max"), Math.max(0, $(this).val())));
    // });
    // $("#id_paid_amount").on('change', function() {
    //     if ($(this).val() != '') {
    //         $("#id_payment_method").select2({ disabled: '' });
    //         $("#id_reference_number").attr("readonly", false);

    //         calculate_balance_amount();
    //     } else {
    //         store_credit = parseFloat($("#id_use_credits").val());
    //         if (store_credit == 0) {
    //             $("#id_payment_method").select2({ disabled: 'readonly' });
    //             $("#id_reference_number").attr("readonly", true);
    //         }
    //     }
    // });

    $("#id_paid_amount").on('input', function() {
        var item_total = parseFloat($("#id_item_total").val());
        var paid_amount = parseFloat($(this).val());

        if (paid_amount > item_total) {
            $(this).val(item_total);
        }
    })

});

function generateBill(url) {

    var count_row = $('.product-row').length;
    if (count_row < 1) {
        $.toast({
            text: "Add at least one product.",
            position: 'bottom-right',
            stack: false,
            icon: 'error',
        })
        return;
    }

    $("#generateBillModal").modal("show");

    data = {}
    data['company_id'] = $("#order_form #id_company").val();
    data['customer_id'] = $("#order_form #id_customer").val();

    if(update_form) {
        data["order_id"] = order_id;
    }

    $.ajax({
        url: url,
        type: "get",
        data: data,
        success: function(data) {
            $("#generate_bill_modal").html(data.html);
            var bill_date = document.querySelector("#generate_bill_modal #id_bill_date");

            $(document).find("#generate_bill_modal #id_payment_method").select2({
                width: "100%",
            }).on("select2:select", function(e){
                $("#order_form #payment_choice").val(e.params.data.id);
            })
            
            var item_total = $("#order_form #id_item_total").val();
            $(document).find("#generate_bill_modal #id_order_total").val(item_total);
            $(document).find("#generate_bill_modal #id_grand_total").val(item_total);

            var now = new Date();
            var day = ("0" + now.getDate()).slice(-2);
            var month = ("0" + (now.getMonth() + 1)).slice(-2);
            var today = now.getFullYear()+"-"+(month)+"-"+(day);

            bill_date.value = today;
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}



function ajax_call_setup() {
    csrf_token = $("#order_form input[name='csrfmiddlewaretoken']").val();
    $.ajaxSetup({
        headers: { "X-CSRFToken": csrf_token }
    });

}


// function get_customers(company_id) {
//     ajax_call_setup();
//     $.ajax({
//         url: get_customers_products_url,
//         type: "post",
//         dataType: "json",
//         data: {
//             'company_id': company_id,
//             'is_update': update_form,
//         },
//         success: function(data) {

//             //data_company_customers = data.company_customers;
//             //$("#order_form #id_customer").append(data_company_customers);

//             // data_company_products = data.company_products;
//             // $("#order_form #id_product").append(data_company_products);

//             $("#id_customer").val(selected_customer).trigger('change');

//             $("#id_customer option[value=" + selected_customer + "]").attr('selected', 'selected');
//         },
//         error: function(xhr, ajaxOptions, thrownError) {
//             console.log(thrownError);
//         }
//     });
// }

function get_warehouse_products($this) {
    ajax_call_setup();
    //   console.log($this.val());
    $.ajax({
        url: $this.attr("data-url"),
        type: "post",
        dataType: "json",
        data: {
            'warehouse_id': $this.val(),
        },
        success: function(data) {

            data_company_products = data.warehouse_products;
            $("#order_form #id_product").append(data_company_products);

            // $("#id_customer").val(selected_customer).change();

            // $("#id_customer option[value="+selected_customer+"]").attr('selected','selected');

            // $("#id_customer").select2().trigger('change');
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}

function get_customer_details(customer_id, url) {
    ajax_call_setup();
    $.ajax({
        url: url,
        type: "post",
        dataType: "json",
        data: {
            'customer_id': customer_id,
        },
        success: function(data) {
            // $("#id_product").append()
            //$("#customer_sales_representative").val(data.customer_sales_representative);
            $("#id_past_due_amount").val(parseFloat(data.past_due_amount));
            $("#id_customer_details").val(data.shipping_address);

            // $("#id_billing_address_line_1").val(data.billing_address.billing_address_line_1);
            // $("#id_billing_address_line_2").val(data.billing_address.billing_address_line_2);
            // $("#id_billing_city").val(data.billing_address.billing_city);
            // $("#id_billing_state").val(data.billing_address.billing_state);
            // $("#id_billing_country").val(data.billing_address.billing_country);
            // $("#id_billing_zip_code").val(data.billing_address.billing_zip_code);


            // $("#id_shipping_address_line_1").val(data.shipping_address.shipping_address_line_1);
            // $("#id_shipping_address_line_2").val(data.shipping_address.shipping_address_line_2);
            // $("#id_shipping_city").val(data.shipping_address.shipping_city);
            // $("#id_shipping_state").val(data.shipping_address.shipping_state);
            // $("#id_shipping_country").val(data.shipping_address.shipping_country);
            // $("#id_shipping_zip_code").val(data.shipping_address.shipping_zip_code);


            // $("#id_use_credits").val(data.total_credit_amount);
            $("#id_product").attr('data-customer-id', customer_id);
            //$("#id_area").val(data.area);


            // $("#id_use_credits").attr("readonly", true);
            // $("#id_use_credits").val("0.00");



            $("#id_available_store_credit").val(data.total_credit_amount);
            $("#id_remaining_store_credit").val(data.total_credit_amount);

            if (data.total_credit_amount > 0) {
                $("#available_store_credits").empty().append("Available Store Credits: <strong>" + data.total_credit_amount + "</strong>");
                $("#id_use_credits").attr("readonly", false);
                $("#id_use_credits").attr("max", data.total_credit_amount);

                //for update view
                if (update_form == true) {

                    used_store_credit = parseFloat($("#id_use_credits").val());
                    used_store_credit = used_store_credit + data.total_credit_amount;
                    $("#available_store_credits").empty().append("Available Store Credits: <strong>" + used_store_credit + "</strong>");
                    $("#id_use_credits").attr("readonly", false);
                    $("#id_use_credits").attr("max", used_store_credit);
                    $("#id_available_store_credit").val(used_store_credit);
                    $("#id_remaining_store_credit").val(data.total_credit_amount);

                }

            } else {

                $("#available_store_credits").empty().append("Available Store Credits: <strong>" + data.total_credit_amount + "</strong>");
                $("#id_use_credits").attr("readonly", false);
                $("#id_use_credits").attr("max", data.total_credit_amount);



                // $("#id_use_credits").attr("readonly", true);
                // // $("#available_store_credits").empty();
                // $("#available_store_credits").empty().append("Available Store Credits: <strong>" + used_store_credit + "</strong>")

                $("#order_form #id_use_credits").val("0.00");

                if (update_form == true) {
                    used_store_credit = parseFloat($("#id_use_credits").val());
                    if (used_store_credit > 0) {
                        $("#id_use_credits").attr("max", used_store_credit);
                        $("#id_use_credits").attr("readonly", false);
                        $("#available_store_credits").empty().append("Available Store Credits: <strong>" + used_store_credit + "</strong>")
                    }
                }

            }

        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}


function get_product_unit_types(product_id, url, no_reset, prd_barcode) {
    ajax_call_setup();

    $.ajax({
        url: url,
        type: "post",
        dataType: "json",
        data: {
            'product_id': product_id,
            'prd_barcode': prd_barcode,
        },
        success: function(data) {
            $("#order_form #id_mrp").val(data.base_price);
            $("#id_available_stock").text(data.stock);
            $("#id_quantity").attr("max", data.stock);
            $("#id_product_brand").val(data.brand_name);
            $("#id_product_vehicle").val(data.vehicle);

            if(is_bill_create){
                $("#order_form #id_unit").val(data.unit);
                $("#order_form #id_price_choice").val("mrp").trigger("change");
            }

            // $("#order_form #id_discount_applied").text(data.applied_discount);
            // $("#order_form #id_brand_primary_discount").val(data.primary_discount);
            // $("#order_form #id_brand_secondary_discount").val(data.secondary_discount);
            // $("#order_form #id_applied_price").text(data.applied_price);
            //$("#order_form #id_brand").val(data.brand).trigger('change');
            //$(document).find("#order_form #id_brand").val().trigger('change');
            
            if (no_reset == false) {
                reset_available_stock_msg();
            }

        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}

function get_product_price_stock(product_id, customer_id, url, unit_type) {
    ajax_call_setup();
    if (unit_type != '') {
        $.ajax({
            url: url,
            type: "post",
            dataType: "json",
            data: {
                // 'warehouse_id': warehouse_id,
                'product_id': product_id,
                'customer_id': customer_id,
                'unit_type': unit_type,
            },
            success: function(data) {
                $("#order_form .cstm-available-stock-msg").empty().append(data.product_price_stock);
                $("#order_form #id_quantity").attr("max", data.quantity_max);
                $("#order_form #id_mrp").val(data.base_price);

            },
            error: function(xhr, ajaxOptions, thrownError) {
                console.log(thrownError);
            }
        });
    }
}

function reset_form() {
    reset_customer();
    reset_product();
    reset_unit_type();
}

function reset_customer() {
    $("#order_form #id_customer").empty().append("<option value=''>---------</option>");
}


function reset_product() {
    $("#order_form #id_product").empty().append("<option value=''>---------</option>");
}

function reset_barcode() {
    $("#order_form #id_barcode").val("");
}

function reset_unit_type() {
    $("#order_form #id_unit").val("");
}

function reset_available_stock_msg() {
    $("#order_form .cstm-available-stock-msg").empty();
}

function reset_quantity() {
    $("#order_form #id_quantity").val("");
}

function reset_brand() {
    $("#order_form #id_brand").val('').trigger('change');
}

function reset_order_totals_and_other_fields() {
    $("#order_form #id_item_total").val("0.00");
    $("#order_form #id_credit_memo").val("0.00");
    $("#order_form #id_shipping_charges").val("0.00");
    $("#order_form #id_adjustments").val("0.00");
    $("#order_form #id_grand_total").val("0.00");
    $("#order_form #id_payable_amount").val("0.00");
    $("#order_form #id_past_due_amount").val("0.00");
    $("#order_form #id_open_balance").val("0.00");
    $("#order_form #id_paid_amount").val("0.00");
    $("#order_form #id_balance_amount").val("0.00");
    $("#order_form #id_reference_number").val("0");
}

function reset_product_fields(){
    $("#id_brand_primary_discount, #id_brand_secondary_discount, #product_base_price, #id_net_price").val("0");
    $("#id_unit, #id_barcode").val("");
    // $("#id_discount_applied, #id_applied_price").text("");
}

function add_product_in_order_list(product_id, quantity, unit_price, add_product_url, special_rate, special_discount, free_quantity, price_type) {
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
            'free_quantity': free_quantity,
            'is_bill_create': is_bill_create,
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
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}


function remove_product_from_selection(id_array) {
    id_array.forEach(function(value, index, array) {
        $("#id_product option[value='" + value + "']").remove();
    });
}

function calculate_order_total() {
    order_sum = 0;
    product_net_prices = [];
    $("#table_added_products .hidden-added-product-net-price").each(function() {
        product_net_prices.push(parseFloat($(this).val()));
    });
    order_sum = product_net_prices.reduce((sum, a) => sum + a, 0);
    $("#order_form #id_item_total").val(order_sum.toFixed(2));
}

function count_table_row_index() {
    indx = 1;
    $(".product-row").each(function() {
        $(this).find("td[data-title='product-id']").text(indx);
        indx += 1;
    });
}

function reset_add_product_fields() {
    $("#id_product").val("").trigger("change");

    $("#order_form #id_quantity").val(0);
    $("#order_form #id_mrp").val(0);
    $("#order_form #id_available_stock").text("0");
    
    $("#id_special_rate").val(0);
    $("#id_special_discount").val(0);
    $("#id_special_rate").removeAttr("disabled");
    $("#id_special_discount").removeAttr("disabled");
    
    $("#id_brand_primary_discount").val(0);
    $("#id_brand_secondary_discount").val(0);
    $("#id_brand_primary_discount, #id_brand_secondary_discount").removeAttr("disabled");
    
    $("#id_discount_applied").text("");
    $("#id_product_brand").val("");
    $("#id_product_vehicle").val("");
    $("#id_product_code").val("");
    $("#id_unit").val("");
    $("#id_previous_price").val(0);
    
    $("#id_free_quantity").val(0);
    $("#id_price_choice").val("mrp").trigger("change");
    $("#btn_add_product").addClass("btn-pointer-events-none");
}

function reset_product_related_fields(){
    $("#order_form #id_quantity").val(0);
    $("#order_form #id_mrp").val(0);
    $("#order_form #id_available_stock").text("0");

    $("#id_brand_primary_discount").val(0);
    $("#id_brand_secondary_discount").val(0);
    $("#id_discount_applied").text("");
    
    $("#id_product_brand").val("");
    $("#id_product_vehicle").val("");
    $("#id_product_code").val("");
    $("#id_unit").val("");
    $("#id_previous_price").val(0);
    
    if(!is_product_update){
        $("#id_free_quantity").val(0);
        $("#id_special_rate").val(0);
        $("#id_special_discount").val(0);
        $("#id_special_rate").removeAttr("disabled");
        $("#id_special_discount").removeAttr("disabled");
        
        $("#id_brand_primary_discount, #id_brand_secondary_discount").removeAttr("disabled");
        $("#id_price_choice").val("mrp").trigger("change");
    }
    $("#btn_add_product").addClass("btn-pointer-events-none");
}

function calculate_product_net_price($this) {
    // console.log($this);
    row_id = $this.attr("data-id");
    prd_quantity = parseInt($this.find(make_input_name(row_id, "__quantity")).val());
    prd_total_pieces = parseInt($this.find("#added_product_total_pieces").val());
    unit_type_pieces = parseInt($this.find(make_input_name(row_id, "__unittypepieces")).val());
    prd_unit_price = parseFloat($this.find(make_input_name(row_id, "__unitprice")).val());
    prd_discount1 = parseFloat($this.find(make_input_name(row_id, "__product_discount1")).val());
    console.log('prd_discount1:', prd_discount1)
    prd_discount2 = parseFloat($this.find(make_input_name(row_id, "__product_discount2")).val());
    console.log('prd_discount:', prd_discount2)
    prd_total_pieces = prd_quantity * unit_type_pieces;
    prd_item_total = prd_total_pieces * prd_unit_price;
    prd_net_price = prd_item_total - ((prd_item_total * prd_discount1) / 100);
    prd_net_price = prd_net_price - ((prd_net_price * prd_discount2) / 100);
    $this.find("[data-title='item-total']").text(parseFloat(prd_item_total).toFixed(2));
    $this.find(make_input_name(row_id, "__itemtotal")).val(prd_item_total.toFixed(2));
    $this.find("#added_product_total_pieces").text(prd_total_pieces);
    $this.find(make_input_name(row_id, "__totalpieces")).val(parseInt(prd_total_pieces));
    $this.find("[data-title='net-price'] .added_product_net_price").text(parseFloat(prd_net_price).toFixed(2));
    $this.find(make_input_name(row_id, "__netprice")).val(prd_net_price.toFixed(2));
    calculate_order_total();
}

function make_input_name($id, $field) {
    return "input[name=" + $id + $field + "]";
}


function reset_form_on_product_company_customer_change() {
    reset_add_product_fields();
    reset_product_fields()
    reset_order_totals_and_other_fields();

    added_product_ids = [];
    $("#order_form #product_id_list").val(added_product_ids);

    $("#table_added_products .product-row").remove();
    if ($('#table_added_products').has('.no-product-row').length == 0) {
        $("#table_added_products tbody").append("<tr class='no-product-row'><td colspan='12'><p>No products added</p></td> </tr>");
    }

}

function simulate_discount(){
    var quantity = parseInt($("#order_form #id_quantity").val());
    const unit_price = parseFloat($("#order_form #product_base_price").val());
    const total_pieces = parseInt($("#order_form #id_total_pieces").val());

    if(!quantity){quantity=0}
    var item_total = unit_price * quantity * total_pieces;

    const brand_primary_discount = parseFloat($("#order_form #id_brand_primary_discount").val());
    const brand_secondary_discount = parseFloat($("#order_form #id_brand_secondary_discount").val());

    var net_amount = calculate_overall_discount(item_total, brand_primary_discount);
    net_amount = calculate_overall_discount(net_amount, brand_secondary_discount);

    return net_amount;
}

// <------------ on change dicount ----------------------------->
function calculate_overall_discount(item_total, discount) {
    var net_amount = item_total - ((item_total * discount) / 100);
    return net_amount.toFixed(2);
}
// <------------end of on change dicount ----------------------------->



// <------------Grand Total Generate ----------------------------->
function calculate_adjustment_and_grand_total() {

    item_total = parseFloat($("#id_item_total").val());
    shipping_charges = parseFloat($("#generate_bill_modal #id_shipping_charges").val());
    packing_charges = parseFloat($("#generate_bill_modal #id_packing_charges").val());

    grand_total = item_total + shipping_charges + packing_charges;

    adjustments = grand_total - Math.round(grand_total);
    if (adjustments < 0) {
        adjustments = -1 * (adjustments);
    } else if (adjustments > 0) {
        adjustments = 1 - adjustments;
        grand_total = grand_total + 1;
    }
    //$("#id_adjustments").val(parseFloat(adjustments).toFixed(2));
    grand_total = Math.round(grand_total);
    $("#generate_bill_modal #id_grand_total").val(parseFloat(grand_total).toFixed(2));
    //$("#id_paid_amount").val(parseFloat(grand_total).toFixed(2))

    $("#id_paid_amount").attr("max", grand_total);

}
// <------------End Of Grand Total Generate ----------------------------->


function calculate_open_balance() {
    payable_amount = parseFloat($("#id_payable_amount").val());
    past_due_amount = parseFloat($("#id_past_due_amount").val());
    open_balance = payable_amount + past_due_amount;
    $("#id_open_balance").val(parseFloat(open_balance).toFixed(2));
    // $("#id_paid_amount").attr('max', open_balance);
    calculate_balance_amount();
}

function calculate_balance_amount() {
    open_balance = parseFloat($("#id_open_balance").val());
    paid_amount = parseFloat($("#id_paid_amount").val());
    balance_amount = open_balance - paid_amount;
    if (balance_amount < 0) {
        $("#id_balance_amount").val(parseFloat(0).toFixed(2));
    } else {
        $("#id_balance_amount").val(parseFloat(balance_amount).toFixed(2));
    }

}

function ajax_call_get_customers_and_warehouse_products(company_id) {
    ajax_call_setup();
    $.ajax({
        url: get_customers_products_url,
        type: "post",
        dataType: "json",
        data: {
            'company_id': company_id,
            'is_update': update_form,
        },
        success: function(data) {
            $("#order_form #id_customer").empty().append("<option value=''>---------</option>");
            $("#order_form #id_product").empty().append("<option value=''>---------</option>");
            data_company_customers = data.company_customers;
            data_company_products = data.company_products;
            data_company_warehouses = data.company_warehouses;
            $("#order_form #id_warehouse").append(data.company_warehouses);
            $("#order_form #id_customer").append(data.company_customers);
            $("#order_form #id_product").append(data.company_products);
            // console.log("selected_customer "+selected_customer)
            $("#order_form #id_warehouse").val(selected_warehouse);
            $("#order_form #id_warehouse").hide();
            // $("#order_form #id_warehouse").select2();

            $("#id_customer").val(selected_customer).change();
            // $("#id_customer option[value="+selected_customer+"]").attr('selected','selected');
            // $("#id_customer").select2().trigger('change');
            if (update_view_first_page_load == true) {
                update_view_first_page_load = false;
            }
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });
}



function ajax_call_order_products_in_update(order_id) {
    selected_product_id = $('#id_product').val();
    ajax_call_setup();
    $.ajax({
        url: update_order_url,
        type: 'post',
        dataType: "json",
        data: {
            'order_id': order_id,
            'is_bill_create': is_bill_create,
        },
        success: function(data) {
            if ($('#table_added_products').has('.no-product-row').length > 0) {
                $('.no-product-row').remove();
            }
            $('#table_added_products').append(data.existing_product_list);
            $("#order_form #product_id_list ").val(data.order__product_ids);
            added_product_ids = data.order__product_ids.map(String);

            //remove_product_from_selection(added_product_ids);
            // calculate_purchase_order_total();
            // count_table_row_index();
            // reset_add_product_fields();
            // remove_product_from_selection(added_product_ids);
        }
    });
}


function ajax_call_get_product_for_order_by_barcode($this) {
    barcode_number = $this.val();
    company_id = $("#order_form #id_company").val();

    if(!company_admin_company_id){
        company_admin_company_id = company_id;
    }
    ajax_call_setup();
    $.ajax({
        url: $this.attr("data-url"),
        type: 'post',
        dataType: "json",
        data: {
            'barcode_number': barcode_number,
            'company_id': company_admin_company_id,
        },
        success: function(data) {
            
            get_product_unit_types(data.product_id, $("#order_form #id_product").attr("data-url"), no_reset = true, barcode_number);

            //$("#order_form #id_product").val(data.product_id).trigger("change");
            //$("#order_form #id_vehicle_name").val(data.product_vehicle);
            
            // product_id = data.product_id;
            // customer_id = $("#id_product").attr("data-customer-id");
            
            // price_stock_url = $("#order_form #id_unit_type").attr("data-url");
            // aunit_type = data.product_unit_type;

            // get_product_price_stock($("#order_form #id_warehouse").val(), product_id, customer_id, price_stock_url, aunit_type);
            // reset_quantity();
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }

    });

}

function validateForm(){
    const inputs = $(document).find("#generate_bill_modal #id_shipping_address input, #generate_bill_modal #id_billing_address input");
    var has_error = false;
    inputs.each(function(index) {
      if($(this).val() == null || $(this).val() == ""){
        const name = $(this).attr("name").replaceAll("_", " ");
        if ($(this).siblings().length <= 0){
          $(this).parent().append(`<span class='text-danger'>Please fill ${name}</span>`);
        }
        has_error = true;
      } else {
        $(this).siblings().remove();
      }
    })
    return has_error;
}

$(document).on('click', "#generate_bill_btn", function() {
    
    if(!valid_due_date) {
        return false;
    }

    $(document).find("#generate_bill_modal").clone(true).appendTo("#order_form");
    $(this).find("#id_grand_total").val($(this).find("#id_item_total").val());
    var form = document.getElementById("order_form");

    var formData = new FormData(form);
    
    $.ajax({
        url: submit_url,
        type: 'post',
        dataType: "json",
        data: formData,
        success: function(data) {
            if (data.bill_pdf_url){
                window.open(data.bill_pdf_url);
            }
            location.href = data.redirect_url;
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        },
        cache: false,
        contentType: false,
        processData: false
    });

});

$(document).on('click', ".submit-btn", function() {
    $("#order_form").find("#id_grand_total").val($("#order_form").find("#id_item_total").val());
    var form = document.getElementById("order_form");

    var formData = new FormData(form);
    formData.append("submit", $(this).val());
    
    $.ajax({
        url: submit_url,
        type: 'post',
        dataType: "json",
        data: formData,
        success: function(data) {
            location.href = data.redirect_url;
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        },
        cache: false,
        contentType: false,
        processData: false
    });
});

function check_available_stock(added_product_ids_updated) {
    //array_length = added_product_ids_updated.length
    is_valid = true
    added_product_ids_updated.forEach((element) => {
        product_id = element
        product_qty = parseInt($("input[name=product_" + product_id + "__quantity" + "]").val())
        available_qty = parseInt($("input[name=product_" + product_id + "__available_stock" + "]").val())
        product_name = $("input[name=product_" + product_id + "__product_name" + "]").val()
        if (product_qty > available_qty) {
            $.toast({
                text: `A Product quantity of ${product_name} is greater than available quantity`,
                position: 'bottom-right',
                stack: false,
                icon: 'error',
            })
            is_valid = false
            return is_valid
        }
    });
    return is_valid

}

$(document).on('click', "#table_added_products .btn-product-remove", function(e) {
    product_id_removed_from_added_list = $(e.target).closest('tr').attr('product-id');
    //console.log("product_id_removed_from_added_list: "+product_id_removed_from_added_list);
    id_index = added_product_ids.indexOf(product_id_removed_from_added_list);
    if (id_index > -1) {
        added_product_ids.splice(id_index, 1);
    }
    $("#order_form #product_id_list").val(added_product_ids);

    reset_add_product_fields();
    //remove_product_from_selection(added_product_ids);

    $(e.target).closest('tr').remove();
    //count_table_row_index();

    calculate_order_total();
});


$('#updateProductModal').on('hidden.bs.modal', function () {
    is_product_update = false;
});


// $(document).on("click", ".btn-product-edit", function(e){
//     is_product_update = true;


//     $("#id_product").val(product_id).trigger("change");

    

//     $("#id_mrp").val(applied_product_price);
//     $("#id_quantity").val(parseInt(qty));
//     $("#id_special_rate").val(special_rate);

//     if (special_rate != 0) {
//         $("#id_special_discount").attr("disabled", true)
//     }

//     if (special_discount != 0) {
//         $("#id_special_rate").attr("disabled", true)
//     }

//     $("#id_special_discount").val(special_discount);

//     if(is_bill_create){
//         var primary_discount = $(document).find(`#id_product_${product_id}__primary_discount`).val()
//         var secondary_discount = $(document).find(`#id_product_${product_id}__secondary_discount`).val()
        
//         $("#id_price_choice").val(price_type).trigger("change");
        
//         $("#id_brand_primary_discount").val(primary_discount);
//         $("#id_brand_secondary_discount").val(secondary_discount);
//     }

//     if(parseFloat(special_discount)>0){
//         $("#id_special_discount").removeAttr("disabled");
//         $("#id_special_rate").attr("disabled", true);
//         $("#id_brand_primary_discount, #id_brand_secondary_discount").attr("disabled", true);
//     }
//     else if(parseFloat(special_rate)>0){
//         $("#id_special_rate").removeAttr("disabled");
//         $("#id_special_discount").attr("disabled", true);
//         $("#id_brand_primary_discount, #id_brand_secondary_discount").attr("disabled", true);
//     }

//     $("#id_free_quantity").val(free_quantity);
//     $("#btn_add_product").removeClass("btn-pointer-events-none");

//     $("#id_product_extra_fields").removeClass("d-none");
//     $("#id_product_add_button").addClass("d-none");
// })




// Update product modal JS

function hide_modal_discounts(){
    $(".discounts").val("0");

    $("#id_order_product_brand_primary_discount").parent().parent().addClass("d-none");
    $("#id_order_product_brand_secondary_discount").parent().parent().addClass("d-none");
    $("#id_order_product_special_rate").parent().parent().addClass("d-none");
    $("#id_order_product_special_discount").parent().parent().addClass("d-none");
}

function show_modal_discounts(){
    $("#id_order_product_brand_primary_discount").parent().parent().removeClass("d-none");
    $("#id_order_product_brand_secondary_discount").parent().parent().removeClass("d-none");
    $("#id_order_product_special_rate").parent().parent().removeClass("d-none");
    $("#id_order_product_special_discount").parent().parent().removeClass("d-none");
}

$(document).on("click", "#btn_update_product", function(){
    var add_product_url = $(this).attr("data-url");

    var product_id = $("#update_product_modal #id_order_product").val();
    var unit_price = $("#update_product_modal #id_order_product_mrp").val();
    var quantity = $(`#update_product_modal #id_order_product_quantity`).val();

    var special_rate = $(`#update_product_modal #id_order_product_special_rate`).val();
    if(!special_rate){special_rate=0;}
    var special_discount = $(`#update_product_modal #id_order_product_special_discount`).val();
    if(!special_discount){special_discount=0;}
    var free_quantity = $(`#update_product_modal #id_order_product_free_quantity`).val();
    if(!free_quantity){free_quantity=0;}

    if(is_bill_create){
        var primary_discount = 0;
        var secondary_discount = 0;
        var price_type = $(`#update_product_modal #id_order_product_price_choice`).val();

        if(price_type == "mrp") {
            primary_discount = $(`#update_product_modal #id_order_product_brand_primary_discount`).val();
            if(!primary_discount){primary_discount=0;}

            secondary_discount = $(`#update_product_modal #id_order_product_brand_secondary_discount`).val();
            if(!secondary_discount){secondary_discount=0;}
        }
        add_product_in_bill_list(product_id, quantity, unit_price, add_product_url, special_rate, special_discount, primary_discount, secondary_discount, free_quantity, price_type);
    }
    else{
        add_product_in_order_list(product_id, quantity, unit_price, add_product_url, special_rate, special_discount, free_quantity, price_type="mrp");
    }

    $("#update_product_modal").html("");
    $("#updateProductModal").modal("hide");
});

function validateModalFields(){

    $("#update_product_modal #id_order_product_quantity").on("keyup", function() {
        var value = parseInt($(this).val());
        var max_value = parseInt($(this).attr("max"));
        
        if(value > max_value){
            $(this).val(max_value);
        }
    });

    $(document).on("input", "#update_product_modal #id_order_product_free_quantity", function(){
        var free_qty = $(this).val();
        if(!free_qty){free_qty=0;}

        var qty = $("#update_product_modal #id_order_product_quantity").val();
        if(!qty){qty=0;}

        if(parseInt(free_qty) < 0){
            $(this).val(0);
        }

        if(parseInt(free_qty) > parseInt(qty)){
            $(this).val(qty);
        }
    });

    $("#update_product_modal #id_order_product").select2({
        width: "100%"
    });

    if(is_bill_create){
        $("#update_product_modal #id_order_product_price_choice").select2({
            width: "100%",
        }).on('select2:select', function() {
            var price_type = $(this).val();

            var product_id = $("#update_product_modal #id_order_product").val();
    
            if(price_type != "mrp"){
                hide_modal_discounts();
            }
            else {
                show_modal_discounts();
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
                            $("#update_product_modal #id_order_product_mrp").val(data.amount);
                        }
                    },
                    error: function(xhr, ajaxOptions, thrownError) {
                        console.log(thrownError);
                    }
                });
            }
        });
    }

    $("#update_product_modal #id_order_product_special_rate").on("input", function(){
        var value = $(this).val();
        if(value) {
            value = parseFloat(value);
            if(value>0){
                $("#id_order_product_special_discount, #id_order_product_brand_primary_discount, #id_order_product_brand_secondary_discount").attr("disabled", "true");
            }
            else {
                $("#id_order_product_special_discount, #id_order_product_brand_primary_discount, #id_order_product_brand_secondary_discount").removeAttr("disabled", "true");
            }
        }
        else {
            $("#id_order_product_special_discount, #id_order_product_brand_primary_discount, #id_order_product_brand_secondary_discount").removeAttr("disabled", "true");
        }
    });

    $("#update_product_modal #id_order_product_special_discount").on("input", function(){
        var value = $(this).val();
        if(value) {
            value = parseFloat(value);
            if(value>100){
                $(this).val(100);
            }
            if(value>0){
                $("#id_order_product_special_rate, #id_order_product_brand_primary_discount, #id_order_product_brand_secondary_discount").attr("disabled", "true");
            }
            else {
                $("#id_order_product_special_rate, #id_order_product_brand_primary_discount, #id_order_product_brand_secondary_discount").removeAttr("disabled");
            }
        }
        else {
            $("#id_order_product_special_rate, #id_order_product_brand_primary_discount, #id_order_product_brand_secondary_discount").removeAttr("disabled");
        }
    });

    $("#update_product_modal #id_order_product_brand_primary_discount, #update_product_modal #id_order_product_brand_secondary_discount").on("input", function(){
        var primary = $("#id_order_product_brand_primary_discount").val();
        var secondary = $("#id_order_product_brand_secondary_discount").val();
   
        if(primary) {
            primary = parseFloat(primary);
            if(primary > 100){
                $("#update_product_modal #id_order_product_brand_primary_discount").val(100);
            }
        }

        if(secondary) {
            secondary = parseFloat(secondary);
            if(secondary > 100){
                $("#update_product_modal #id_order_product_brand_secondary_discount").val(100);
            }
        }

        if(primary && secondary) {
            primary = parseFloat(primary);
            secondary = parseFloat(secondary);
    
            if(primary>0 || secondary>0){
                $("#id_order_product_special_rate, #id_order_product_special_discount").attr("disabled", "true");
            }
            else {
                $("#id_order_product_special_rate, #id_order_product_special_discount").removeAttr("disabled");
            }
        }
        else {
            if(primary){
                primary = parseFloat(primary);
                if(primary>0) {
                    $("#id_order_product_special_rate, #id_order_product_special_discount").attr("disabled", "true");
                }
                else {
                    $("#id_order_product_special_rate, #id_order_product_special_discount").removeAttr("disabled");
                }
            }
            else if(secondary) {
                secondary = parseFloat(secondary);
                if(primary>0) {
                    $("#id_order_product_special_rate, #id_order_product_special_discount").attr("disabled", "true");
                }
                else {
                    $("#id_order_product_special_rate, #id_order_product_special_discount").removeAttr("disabled");
                }
            }
            else {
                $("#id_order_product_special_rate, #id_order_product_special_discount").removeAttr("disabled");
            }
        }
    });
}

$(document).on("click", ".btn-product-edit", function(e){
    is_product_update = true;

    var product_id = $(e.target).closest('tr').attr('product-id');
    var customer_id = $(document).find("#id_customer").val();
    var applied_product_price = $(document).find(`#id_product_${product_id}__applied_product_price`).val()
    var free_quantity = $(document).find(`#id_product_${product_id}__free_quantity`).val()
    var qty = $(document).find(`#id_product_${product_id}__quantity`).val()
    var price_type = $(document).find(`#id_product_${product_id}__price_type`).val()
    var special_rate = $(document).find(`#id_product_${product_id}__special_rate`).val()
    var special_discount = $(document).find(`#id_product_${product_id}__special_discount`).val()
    var primary_discount = 0;
    var secondary_discount = 0;

    if(is_bill_create){
        primary_discount = $(document).find(`#id_product_${product_id}__primary_discount`).val()
        secondary_discount = $(document).find(`#id_product_${product_id}__secondary_discount`).val()
    }

    $.ajax({
        url: update_order_product_url,
        type: "get",
        dataType: "json",
        data: {
            'is_bill_create': is_bill_create,
            'product_id': product_id,
            'customer_id': customer_id,
            'price_type': price_type,
            'applied_product_price': applied_product_price,
            'qty': qty,
            'free_quantity': free_quantity,
            'special_rate': special_rate,
            'special_discount': special_discount,
            'primary_discount': primary_discount,
            'secondary_discount': secondary_discount,
        },
        success: function(data) {
            $("#update_product_modal").html(data.html);
            $("#updateProductModal").modal("show");

            validateModalFields();

            if(parseFloat(special_discount)>0){
                $("#id_order_product_special_discount").removeAttr("disabled");
                $("#id_order_product_special_rate").attr("disabled", true);
                $("#id_order_product_brand_primary_discount, #id_order_product_brand_secondary_discount").attr("disabled", true);
            }
            else if(parseFloat(special_rate)>0){
                $("#id_order_product_special_rate").removeAttr("disabled");
                $("#id_order_product_special_discount").attr("disabled", true);
                $("#id_order_product_brand_primary_discount, #id_order_product_brand_secondary_discount").attr("disabled", true);
            }
            else if(parseFloat(primary_discount)>0 || parseFloat(secondary_discount)>0) {
                $("#id_order_product_brand_primary_discount, #id_order_product_brand_secondary_discount").removeAttr("disabled");
                $("#id_order_product_special_rate, #id_order_product_special_discount").attr("disabled", true);
            }
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(thrownError);
        }
    });

});