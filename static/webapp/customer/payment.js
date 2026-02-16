function loadCustomer() {
    company_name = document.getElementById("company").value
    
    $.ajax({
        type:"GET",
        url:url,
        data:{
            "company_name":company_name,
        },
        success: function (data){
            $("#id_customer_name").empty().append("<option value = ''>---------</option> ")
            var list = data;
            list.customer_data.forEach(element => {
                var option = document.createElement("option");
                option.value = element.id;
                option.text = element.customer_name;
                id_customer_name.options.add(option);
            });
        }
    })
    
}

$(document).ready(function () {
    check_no = document.getElementById("id_check_no");
    check_no.style.display = 'none';

}


)
$("#id_payment_mode").on("change", function(){
    if($("#id_payment_mode").val() === "check"){
        check_no = document.getElementById("id_check_no");
        check_no.style.display = 'block';
    }
    else
    {
        check_no.style.display = 'none';
    }
})

function autoSelectBills(total_amount){
    var table_rows = $(document).find("#table_customer_payment>tbody>tr");

    table_rows.each(function(index, tr) {
        if(total_amount > 0) {

            var order_bill_id = $(this).data("id");
            
            if($(this).hasClass("customer-past-due")){
                var past_due_amount = $(this).find("#id_past_due_amount");
                var past_due = parseInt(past_due_amount.val());

                console.log("past_due ", past_due);
                $(document).find(`#id_customer_checkbox`).prop('checked', true);
                
                if(total_amount >= past_due){
                    $("#id_customer__paid_amount").val(past_due);
                    $("#id_customer__due_balance").val(0);
                    total_amount -= past_due;
                }
                else {
                    $("#id_customer__paid_amount").val(total_amount);
                    $("#id_customer__due_balance").val(past_due - total_amount);
                    total_amount = 0;
                }
            }
            else {
                var due_amount = parseFloat($(document).find(`#id_${order_bill_id}__due_amount`).val());
    
                $(document).find(`#id_${order_bill_id}__checkbox`).prop('checked', true);
                if(added_bill_ids.indexOf(order_bill_id) == -1) {
                    added_bill_ids.push(order_bill_id);
                }
    
                if(total_amount >= due_amount) {
                    $(document).find(`#id_${order_bill_id}__paid_amount`).val(due_amount);
                    $(document).find(`#id_${order_bill_id}__due_balance`).val(0);
                    total_amount -= due_amount;
                }
                else {
                    $(document).find(`#id_${order_bill_id}__paid_amount`).val(total_amount);
                    $(document).find(`#id_${order_bill_id}__due_balance`).val(due_amount - total_amount);
                    total_amount = 0;
                }
            }
        }
    });

    if(total_amount <= 0) {
        $(".checkbox").not(':checked').prop("disabled", true);
        $(".customer_checkbox").not(':checked').prop("disabled", true);
    }

    $(document).find("#id_credit_amount").val(total_amount);
    $("#customer_bill_id_list").val(added_bill_ids);

    return total_amount;
  }