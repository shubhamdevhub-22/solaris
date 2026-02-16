
var valid_due_date = true;

$(document).on("input", "#id_due_days", function(){
    var bill_date = document.querySelector("#generate_bill_modal #id_bill_date");
    var due_days = document.querySelector("#generate_bill_modal #id_due_days");
    var due_date = document.querySelector("#generate_bill_modal #id_due_date");
    
    if(bill_date && due_days) {
        if(due_days.value){
            due_days = parseInt(due_days.value);
        }
        else {
            return;
        }
        
        bill_date = new Date(bill_date.value);
        var due_date = bill_date;
        due_date.setDate(bill_date.getDate()+due_days);
        
        var day = ("0" + due_date.getDate()).slice(-2);
        var month = ("0" + (due_date.getMonth() + 1)).slice(-2);

        document.querySelector("#generate_bill_modal #id_due_date").value = due_date.getFullYear()+"-"+(month)+"-"+(day);
        
        bill_date = document.querySelector("#generate_bill_modal #id_bill_date")
        due_date = document.querySelector("#generate_bill_modal #id_due_date")

        if(bill_date.parentElement.children.length > 1){
            bill_date.parentElement.removeChild(bill_date.parentElement.lastChild);
        }
        if(due_date.parentElement.children.length > 1){
            due_date.parentElement.removeChild(due_date.parentElement.lastChild);
        }
        valid_due_date = true;
    }
});


$(document).on("input", "#id_due_date, #id_bill_date", function(){
    var due_date = document.querySelector("#generate_bill_modal #id_due_date");
    var bill_date = document.querySelector("#generate_bill_modal #id_bill_date");

    if(due_date && due_date.value){
        due_date = new Date(due_date.value);
        
        if(bill_date && bill_date.value){
            bill_date = new Date(bill_date.value);
            const diffTime = Math.abs(due_date - bill_date);
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
            document.querySelector("#generate_bill_modal #id_due_days").value = diffDays;

            if(due_date < bill_date){
                if($(this).parent().children().length <= 1){
                    $(this).parent().append("<span class='text-danger'>Due date does not smaller than bill date.</span>");
                }
                valid_due_date = false;
            }
            else{
                bill_date = document.querySelector("#generate_bill_modal #id_bill_date");
                if(bill_date.parentElement.children.length > 1){
                    bill_date.parentElement.removeChild(bill_date.parentElement.lastChild);
                }

                due_date = document.querySelector("#generate_bill_modal #id_due_date");
                if(due_date.parentElement.children.length > 1){
                    due_date.parentElement.removeChild(due_date.parentElement.lastChild);
                }
                valid_due_date = true;
            }
        }
    }
});
