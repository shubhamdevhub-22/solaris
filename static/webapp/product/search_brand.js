$('#id_brand').select2({
    width: "100%",
    ajax: {
        url: search_url,
        data: function (params) {
            var query = {
                search: params.term,
                type: 'public',
                model: 'brand'
            }
            const company = $("#id_company").val()
            if(company){
                query["company"] = company;
            }
            return query;
        },
        processResults: function (data) {
            return {
              results: data.items
            };
        },
    },
});

$('#id_vehicle').select2({
    width: "100%",
    ajax: {
        url: search_url,
        data: function (params) {
            var query = {
                search: params.term,
                type: 'public',
                model: 'vehicle'
            }
            const company = $("#id_company").val()
            if(company){
                query["company"] = company;
            }
            return query;
        },
        processResults: function (data) {
            return {
            results: data.items
            };
        },
    },
});