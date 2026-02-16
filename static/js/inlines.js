var utils = {


    inlineFormSLMEmailAdd: function(id, mgmt_form_id, callback) {
        $(document).on('click', '#add-email-inline', function() {
            event.preventDefault();
            var template_markup = $(`#${id}-template`).html();
            var count = parseInt($(`#id_${mgmt_form_id}-TOTAL_FORMS`).attr('value'), 10);
            var compiled_template = template_markup.replace(/__prefix__/g, count);
            $(`#${id}-table tbody`).append(compiled_template);
            $(`#id_${mgmt_form_id}-TOTAL_FORMS`).attr('value', count + 1);

            if (callback != undefined) {
                callback();
            }
            $('.select2-data-array').select2({
                width: "100%",
            });

            const input_5 = document.querySelector(`#id_customer-${count}-mobile_no`)

            window.intlTelInput(input_5, {

                onlyCountries: ['in'],
                separateDialCode: true,
                nationalMode: false,
            })
        });
    },


    inlineFormRemove: function(table = null) {
        $(document).on('click', '.inlineform-remove', function() {
            $(this).parent().parent().hide();
        });
    },

    inlineFormSLMDiscountAdd: function(id, mgmt_form_id, callback) {
        $(document).on('click', '#add-discounts-inline', function() {
            event.preventDefault();
            var template_markup =  $(`#${id}-template`).html();
            var count =  parseInt($(`#id_${mgmt_form_id}-TOTAL_FORMS`).attr('value'), 10);
            var compiled_template = template_markup.replace(/__prefix__/g, count);
            $(`#${id}-table tbody`).append(compiled_template);
            $(`#id_${mgmt_form_id}-TOTAL_FORMS`).attr('value', count + 1);
        
            if (callback != undefined) {
                callback();
            }

            $(document).find(`#id_customer_discounts-${count}-brand`).select2({
                width: "100%",
                placeholder: "Select Brand",
                ajax: {
                    url: brand_search_url,
                    data: function (params) {
                        var query = {
                            search: params.term,
                            type: 'public'
                        }
                        query["company"] = $("#id_company").val();
                        return query;
                    },
                    processResults: function (data) {
                        return {
                          results: data.items
                        };
                    },
                },
            }).on("select2:select", function(e){
                const row_id = $(this).data("id");
                $(document).find(`#id_customer_discounts-${row_id}-discount`).empty();
                $(document).find(`#id_customer_discounts-${row_id}-discount_percent`).val("");
            });
            $(document).find(`#id_customer_discounts-${count}-discount`).select2({
                width: "100%",
                placeholder: "Select Discount",
                ajax: {
                    url: discount_search_url,
                    data: function (params) {
                        var query = {
                            search: params.term,
                            type: 'public'
                        }
                        const row_id = $(this).data("id");
                        const brand_id = $(document).find(`#id_customer_discounts-${row_id}-brand`).val();
                        if(brand_id){
                            query["brand"] = brand_id;
                        }
                        return query;
                    },
                    processResults: function (data) {
                        return {
                          results: data.items
                        };
                    },
                },
            }).on("select2:select", function(e){
                const row_id = $(this).data("id");
                $(document).find(`#id_customer_discounts-${row_id}-discount_percent`).val(e.params.data.discount);
            });
        });
    }

}


// this code for checkbox in inline view contact details
        // when user click one check then move two send so when first is disable
    var $checks = $('input[type="checkbox"]');
    $checks.click(function() {
    $checks.not(this).prop("checked", false);
    });
//----END---

    $(document).on('click', 'input[type="checkbox"]', function() {      
        $('input[type="checkbox"]').not(this).prop('checked', false);      
    });
    
    // $('.id_customer-NaN-is_default').on('change', function() {
    //     $('.id_customer-NaN-is_default').not(this).prop('checked', false);  
    // });

    