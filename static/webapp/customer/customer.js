const csrf_token = $("#customer-form input[name='csrfmiddlewaretoken']").val();

$('.select2-list').select2({
    width: "100%",
});


$('#company-dropdown').select2({
  width: "100%",
});


$('.select2-data-array').select2({
  width: "100%",
});

function search_discount(){
    $(document).find(`.discount-select2-list`).select2({
        width: "100%",
        placeholder: "------",
        allowClear: true,
        ajax: {
            url: discount_search_url,
            data: function (params) {
                var query = {
                    search: params.term,
                    type: 'public'
                }
                const brand_id = $(this).data("brand_id");
                if(brand_id){
                    query["brand_id"] = brand_id;
                }
                const discount = $(this).data("discount");
                query["discount_type"] = discount;
                query["company"] = $("#id_company").val();
                return query;
            },
            processResults: function (data) {
                return {
                    results: data.items
                };
            },
        },
    }).on("select2:select select2:clear", function(e){
        const brand_id = $(this).data("brand_id");
        const discount = $(this).data("discount");
        var discount_per = e.params.data.discount;
        if(!discount_per){
            discount_per = 0
        }

        if(discount == 'primary'){
            $(document).find(`#id_percent-${brand_id}-primary_discount`).val(discount_per);
        }
        else{
            $(document).find(`#id_percent-${brand_id}-secondary_discount`).val(discount_per);
        }
    })

}
search_discount();

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
})

// var total_forms = parseInt($("#id_customer_discounts-TOTAL_FORMS").val());

// for(let count=0; count<total_forms; count++){
//     $(document).find(`#id_customer_discounts-${count}-brand`).select2({
//       width: "100%",
//       placeholder: "Select Brand",
//       ajax: {
//           url: brand_search_url,
//           data: function (params) {
//               var query = {
//                   search: params.term,
//                   type: 'public'
//               }
//               query["company"] = $("#id_company").val();
//               return query;
//           },
//           processResults: function (data) {
//               return {
//                 results: data.items
//               };
//           },
//       },
//     }).on("select2:select", function(e){
//       $(document).find(`#id_customer_discounts-${count}-discount`).empty();
//       $(document).find(`#id_customer_discounts-${count}-discount_percent`).val(0);
//       $(document).find(`#id_customer_discounts-${count}-additional_discount`).val(0);
//     });
// }


var id = 0;

const input_1 = document.querySelector("#id_phone_1")
const input_2 = document.querySelector("#id_phone_2")
const input_3 = document.querySelector("#id_mobile")

window.intlTelInput(input_1, {    
    onlyCountries: ['in'],
    separateDialCode: true,
    nationalMode: false,
})

window.intlTelInput(input_2, {    
    onlyCountries: ['in'],
    separateDialCode: true,
    nationalMode: false,
})

window.intlTelInput(input_3, {    
    onlyCountries: ['in'],
    separateDialCode: true,
    nationalMode: false,
})

const inputs = document.querySelectorAll(".mobile-number");
    inputs.forEach(input => {
      window.intlTelInput(input, {
        onlyCountries: ['in'],
        separateDialCode: true,
        nationalMode: false,
    });
});


$(document).ready(function(){
    if(update_form){
        // $.ajax({
        //     type: "POST",
        //     url: customer_discount_url,
        //     data:{
        //         "customer_id": customer_id,
        //         "csrfmiddlewaretoken": csrf_token,
        //     },
        //     success: function (data){
        //       $("#discount-table").html(data.discount_table);
        //       search_discount();
        //     }
        // });
    }

    $(document).on("input", ".customer-discount", function(){
        var value = $(this).val();

        if(value){
            value = parseFloat(value);
            if(value > 100){
                $(this).val(100);
            }
        }
    })
})