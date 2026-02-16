var payment_amount = $("#id_payment_amount").val();
var added_bill_ids = [];

function loadVendortablelist() {
  vendor_id = $("#id_vendor").val();
  //console.log("vendor_id:", vendor_id);

  $.ajax({
    type: "GET",
    url: url,
    data: {
      vendor_id: vendor_id,
    },
    success: function (data) {
      //console.log("data:", data);
      $("#extended").html(data);
      var $response = $(data);
      var inputValue = $response.find("#id_total_due_amount").val();
      $(".checkbox").prop("disabled", true);
      $(".vendor-bill-save-btn").prop("disabled", true);
      
      if (inputValue > 0) {
        $("#id_due_amount").val(inputValue);
      } else {
        $("#id_due_amount").val(0);
      }
    },
  });
}


var added_bill_ids = [];
$(document).ready(function () {
  //$("#id_payment_amount").prop("disabled", true);
  //$("#id_payment_mode").prop("disabled", true);
});

// $("#id_payment_mode").on("change", function (e) {
//   $("#id_payment_amount").prop("disabled", false);
// });

$("#id_vendor").on("change", function (e) {
  $("#id_payment_mode").prop("disabled", false);
  $("#id_payment_amount").prop("disabled", false);
  $("#id_payment_amount").val(0);

});

var td_checkbox = null;
$("#id_payment_amount").on("focusout ", function (e) {
  $(".checkbox").prop("disabled", false);
  
  $(this).on("keyup", function(){
    loadVendortablelist()
  })
  validation_pay_amount();
  added_bill_ids.length = 0;

  // td_checkbox = $('#id_checkbox_td');
  // var checkbox = td_checkbox.find('input[type="checkbox"]');
  // console.log('checkbox:', checkbox)
  // checkbox.on('change', function() {
  //     if (checkbox.is(':checked')) {

  //         calculate_pay_amount();
  //         console.log('calculate_pay_amount:')
  //     }
  //   });
});

// function calculate_pay_amount() {
//   payment_amount = $("#id_payment_amount").val();
//   console.log("payment_amount:", payment_amount);
//   // console.log(td_checkbox)
//   var nextRow = $(this).closest("tr").next("tr");
//   nextRow.find("td").eq(1).text(payment_amount);
// }

function validation_pay_amount() {
  due_amount = $("#id_due_amount").val();
  //console.log("due_amount:", due_amount);
  payment_amount = $("#id_payment_amount").val();
  //console.log("payment_amount:", payment_amount);
  if (parseInt(payment_amount) > parseInt(due_amount)) {
    $.toast({
      text: "Payment Amount is not Greater than the Due Amount",
      position: "bottom-right",
      stack: false,
      icon: "error",
    });
    $("#id_payment_amount").val(0);
    $(".checkbox").prop("disabled", true);
};
if (parseInt(payment_amount) <= 0 ) {
  $.toast({
    text: "Payment Amount is not less than the 0",
    position: "bottom-right",
    stack: false,
    icon: "error",
  });
  $("#id_payment_amount").val(0);
  $(".checkbox").prop("disabled", true);
};
}



// function tabel_row_select(){
//   // $(document).ready(function (e) { 
//     // $("#table_vendor_payment .vendor-row").click(function(){
//   $("#table_vendor_payment .vendor-row").on("click",function (e) {
//       if (e.target && $(e.target).hasClass("checkbox")) {
//             $(e.target).on('change',function(){
//                 if ($(e.target).is(':checked')) {
//                     console.log("%ctarget", 'color: red');
//                     vendorbill_id = $(e.target).closest("tr").attr("data-id");
//                     console.log("vendorbill_id:", vendorbill_id);
      
//                     console.log('payment_amount:', payment_amount)
      
//                     due_amount = $("#id_" + vendorbill_id  + "__due_amount")
      
//                     console.log('due_amount:', due_amount.val())
//                     paid_amount = $("#id_" + vendorbill_id  + "__paid_amount")
      
//                     due_balance = $("#id_" + vendorbill_id  + "__due_balance")
//                     console.log('due_balance:', due_balance.val())
      
      
//                     console.log('paid_amount:', paid_amount.val())
//                     if (parseInt(payment_amount) >= parseInt(due_amount.val()) ){
//                       paid_amount.val(due_amount.val())
//                       due_balance.val(parseInt(due_amount.val()) - parseInt(paid_amount.val()))
//                       payment_amount = parseInt(payment_amount) - parseInt(paid_amount.val())
//                       console.log('payment_amount:', payment_amount)
      
//                       if (parseInt(payment_amount) < 0  ) {
//                         $(".checkbox").prop("disabled", true);
//                       } 
//                     } else if (parseInt(payment_amount) <= parseInt(due_amount.val()) ){
//                         paid_amount.val(parseInt(payment_amount)) 
//                         due_balance.val(parseInt(due_amount.val()) - parseInt(paid_amount.val()))
//                         console.log('due_balance:', due_balance.val())
//                         payment_amount = parseInt(payment_amount) - parseInt(paid_amount.val())
                        
//                         console.log('payment_amount:', payment_amount)
//                     }
//                 } else {
//                     console.log("%cUntarget", 'color: red' )
//                     vendorbill_id = $(e.target).closest("tr").attr("data-id");
//                     console.log("vendorbill_id:", vendorbill_id);
      
      
//                     due_amount = $("#id_" + vendorbill_id  + "__due_amount")
//                     console.log('due_amount:', due_amount.val())
      
//                     paid_amount = $("#id_" + vendorbill_id  + "__paid_amount")
//                     console.log('paid_amount:', paid_amount.val())
      
//                     due_balance = $("#id_" + vendorbill_id  + "__due_balance")
//                     console.log('due_balance:', due_balance.val())
      
      
//                     console.log('paid_amount:', paid_amount.val())
//                     payment_amount += parseInt(paid_amount.val())
//                     console.log('payment_amount:', payment_amount)
//                     paid_amount.val(0)
//                     due_balance.val(parseInt(due_amount.val()))
      
      
//                 }
            
//             })
//        }
//       }
//       );
//     // })
// }

$(document).on("change", ".checkbox", function (){
  if ($(this).is(':checked')) {
    //console.log("%ctarget", 'color: red');
    vendorbill_id = $(this).closest("tr").attr("data-id");
    //console.log("vendorbill_id:", vendorbill_id);
    

    //console.log('payment_amount:', payment_amount)

    due_amount = $("#id_" + vendorbill_id  + "__due_amount")

    //console.log('due_amount:', due_amount.val())
    paid_amount = $("#id_" + vendorbill_id  + "__paid_amount")

    due_balance = $("#id_" + vendorbill_id  + "__due_balance")
    //console.log('due_balance:', due_balance.val())


    //console.log('paid_amount:', paid_amount.val())
    if (parseInt(payment_amount) >= parseInt(due_amount.val()) ){
      paid_amount.val(due_amount.val())
      due_balance.val(parseInt(due_amount.val()) - parseInt(paid_amount.val()))
      payment_amount = parseInt(payment_amount) - parseInt(paid_amount.val())
      //console.log('payment_amounttttt:', payment_amount)

    
    } else if (parseInt(payment_amount) <= parseInt(due_amount.val()) ){
        paid_amount.val(parseInt(payment_amount)) 
        due_balance.val(parseInt(due_amount.val()) - parseInt(paid_amount.val()))
        //console.log('due_balance:', due_balance.val())
        payment_amount = parseInt(payment_amount) - parseInt(paid_amount.val())
        //console.log('payment_amount:', payment_amount)
    }

  } else {
      //console.log("%cUntarget", 'color: red' )  
      vendorbill_id = $(this).closest("tr").attr("data-id");
      //console.log("vendorbill_id:", vendorbill_id);


      due_amount = $("#id_" + vendorbill_id  + "__due_amount")
      //console.log('due_amount:', due_amount.val())

      paid_amount = $("#id_" + vendorbill_id  + "__paid_amount")
      //console.log('paid_amount:', paid_amount.val())

      due_balance = $("#id_" + vendorbill_id  + "__due_balance")
      //console.log('due_balance:', due_balance.val())


      //console.log('paid_amount:', paid_amount.val())
      payment_amount += parseInt(paid_amount.val())
      //console.log('payment_amount:', payment_amount)
      paid_amount.val(0)

      due_balance.val(parseInt(due_amount.val()))
      if (parseInt(payment_amount) > 0  ) {
        $(".checkbox").prop("disabled", false);
        $(".vendor-bill-save-btn").prop("disabled", true);

      }
  }

  if(parseInt(payment_amount) === 0 ){
    $(".vendor-bill-save-btn").prop("disabled", false);
    //console.log("payment_amount is 0 now")
    $(".checkbox").prop("disabled", true);
    $(this).prop("disabled", false);

  }

})

// function bill_id_list(){
$(document).on("change", ".checkbox", function(){
    if ($(this).is(':checked')) {
        vendorbill_id = $(this).closest("tr").attr("data-id");
        //console.log(vendorbill_id)
        added_bill_ids.push(vendorbill_id)
        //console.log('added_bill_ids:', added_bill_ids)
} else {
  added_bill_ids.pop(vendorbill_id)
  //console.log('added_bill_ids:', added_bill_ids)
}
//console.log(added_bill_ids)
$("#vendor_bill_id_list").val(added_bill_ids)
//console.log('vendor_bill_id_list:', $("#vendor_bill_id_list").val())
})
// }


// if (parseInt(payment_amount) <= 0  ) {
//   //console.log("trueeeee")
//   $(".checkbox").prop("disabled", true);
//   $(this).prop("disabled", false);
//   $(".vendor-bill-save-btn").prop("disabled", false);
// } 

