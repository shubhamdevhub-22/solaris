document.body.addEventListener("productVehicleCreate", function(evt){
    $("#id_vehicle").append(evt.detail.option);
    $("#id_vehicle").val(evt.detail.vehicle_id);

    $('#ProductVehicleForm').modal('hide');
    
    $.toast({
      text: evt.detail.message,
      position: 'bottom-right',
      stack: false,
      icon: evt.detail.level,
    });
});

function openModal(){

    if(is_superuser){
      const company = $("#id_product_form").find("#id_company").val();
      
      if(!company){
        $.toast({
          text: "Please select company !!!",
          position: 'bottom-right',
          stack: false,
          icon: "error",
        });
        return;
      }
    }

    $('#ProductVehicleForm').modal('show');
    htmx.ajax('GET', add_vehicle_url, '#add_product_vehicle_modal').then(()=>{
        const select = document.querySelector("#add_product_vehicle_modal #id_company")
        var opt = document.createElement('option');
        opt.value = $("#id_product_form #id_company").val();
        opt.innerHTML = "";
        select.appendChild(opt);
    });
}