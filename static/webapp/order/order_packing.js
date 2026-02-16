$("#order_products_list").select2({
    width: "100%",
});

$(document).ready(function() {
    $("#order_products_list").on("change", function() {
        selected_product_id = $(this).val();
        if (selected_product_id != '') {
            $("#set_packing_quantity").show();
            //quantity = $("#product_row_" + selected_product_id).data("quantity");
            //console.log(quantity, "----")
            unpacked_qty = $("#unpackedquantity_" + selected_product_id).val()
            $("#unpacked_quantity").val(unpacked_qty);
            $("#packed_quantity").attr('max', unpacked_qty);

        } else {
            $("#set_packing_quantity").hide();

        }
        // set_order_product_packing_detail(product_id = selected_product_id, barcode = null);
    });
    $("#order_product_barcode").on('keyup', function() {
        product_barcode = $(this).val();
        if (product_barcode != '') {
            set_order_product_packing_detail(barcode = product_barcode);
        }
    });
    $("#btn_set_packed_qty").on("click", function() {
        selected_product_id = $("#order_products_list").val();
        packed_quantity = $("#packed_quantity").val();
        if (selected_product_id != '' & packed_quantity != '0') {
            before_pack = $("input#packedquantity_" + selected_product_id).val();
            $("input#packedquantity_" + selected_product_id).val(parseInt(before_pack) + parseInt(packed_quantity));
            $("#packed_quantity").val(0);
            $("#order_product_barcode").val("");
            before_add = $("input#unpackedquantity_" + selected_product_id).val();
            //total_quantity = $("#product_row_" + selected_product_id).data("quantity");
            $("input#unpackedquantity_" + selected_product_id).val(parseInt(before_add) - parseInt(packed_quantity));
            $("#set_packing_quantity").hide();
            $('#order_products_list').val(null).trigger('change');
        }
    });
    $("#packed_quantity").on("mouseup keyup focusout", function() {
        $(this).val(Math.min($(this).attr("max"), Math.max(0, $(this).val())));
    });
});

function set_order_product_packing_detail(barcode) {
    //console.log("barcode " + barcode);

    $.ajax({
        url: packing_url,
        type: "get",
        dataType: "json",
        data: {
            'barcode': barcode,
            'order_id': order_id,
        },
        success: function(data) {
            if (data.message) {
                $.toast({
                    text: data.message,
                    position: 'bottom-right',
                    stack: false,
                    icon: 'error'
                })
                $("#packed_quantity").val(0);

                $("#set_packing_quantity").hide();
                $('#order_products_list').val(null).trigger('change');

            } else {
                //console.log("data.product_id " + data.product_id);
                $('#order_products_list').val(data.product_id).trigger('change');

            }
        },
        error: function(xhr, ajaxOptions, thrownError) {
            //console.log(thrownError);
        }
    });
}