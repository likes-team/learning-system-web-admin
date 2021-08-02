$(document).ready(function(){

    $("#lbl_search_client").html("Search Oriented Students");

    $("#amount").change(function(){
        var payment_mode = $('input[name="payment_modes"]:checked').val();
        var balance;

        if (payment_mode == "full_payment"){
            balance = 7000 - $(this).val();
          
        } else if (payment_mode == "installment") {
            balance = 7800 - $(this).val();
        } else if (payment_mode == "full_payment_promo"){
            balance = 5500 - $(this).val();
        } else if (payment_mode == "installment_promo"){
            balance = 6300 - $(this).val();
        }

        $("#balance").val(balance);
    });

    $('#amount').on('input', function () {
        var payment_mode = $('input[name="payment_modes"]:checked').val();
        
        var value = $(this).val();
        
        if (payment_mode == "full_payment"){
            if ((value !== '') && (value.indexOf('.') === -1)) {
            
                $(this).val(Math.max(Math.min(value, 7000), -7000));
            }
        } else if (payment_mode == "full_payment_promo"){
            if ((value !== '') && (value.indexOf('.') === -1)) {
            
                $(this).val(Math.max(Math.min(value, 5500), -5500));
            }
        } else if (payment_mode == "installment") {
            if ((value !== '') && (value.indexOf('.') === -1)) {
            
                $(this).val(Math.max(Math.min(value, 4000), -4000));
            }
        } else if (payment_mode == "installment_promo"){
            if ((value !== '') && (value.indexOf('.') === -1)) {
            
                $(this).val(Math.max(Math.min(value, 4000), -4000));
            }
        }
    
    });

    $('input[type=radio][name=payment_modes]').change(function() {
        var balance;

        if (this.value == 'full_payment') {
            $("#amount").val(7000);
            $("#amount").prop('readonly', true);

            balance = 7000 - $("#amount").val();

            $('#book_none').prop('checked', false);
            $('#book1').prop('checked', true);
            $('#book2').prop('checked', false);

            $("#uniform_m").prop("checked", true);

            $('#id_card').prop('checked', false);
            $('#id_lace').prop('checked', false);
        }
        else if (this.value == 'installment') {
            $("#amount").val(1000);
            $("#amount").prop('readonly', false);

            balance = 7800 - $("#amount").val();

            $('#book_none').prop('checked', true);
            $('#book1').prop('checked', false);
            $('#book2').prop('checked', false);

            $("#uniform_none").prop("checked", true);

            $('#id_card').prop('checked', false);
            $('#id_lace').prop('checked', false);
        } else if(this.value == 'premium'){
            $("#amount").val(8500);
            $("#amount").prop('readonly', true);

            balance = 8500 - $("#amount").val();

            $('#book_none').prop('checked', false);
            $('#book1').prop('checked', true);
            $('#book2').prop('checked', true);

            $("#uniform_m").prop("checked", true);

            $('#id_card').prop('checked', true);
            $('#id_lace').prop('checked', true);
        } else if (this.value == 'full_payment_promo') {
            $("#amount").val(5500);
            $("#amount").prop('readonly', true);

            balance = 5500 - $("#amount").val();

            $('#book_none').prop('checked', false);
            $('#book1').prop('checked', true);
            $('#book2').prop('checked', false);

            $("#uniform_m").prop("checked", true);

            $('#id_card').prop('checked', false);
            $('#id_lace').prop('checked', false);
        } else if (this.value == 'installment_promo') {
            $("#amount").val(4000);
            $("#amount").prop('readonly', false);

            balance = 6300 - $("#amount").val();

            $('#book_none').prop('checked', true);
            $('#book1').prop('checked', false);
            $('#book2').prop('checked', false);

            $("#uniform_none").prop("checked", true);

            $('#id_card').prop('checked', false);
            $('#id_lace').prop('checked', false);
        } else if(this.value == "premium_promo"){
            $("#amount").val(7000);
            $("#amount").prop('readonly', true);

            balance = 7000 - $("#amount").val();

            $('#book_none').prop('checked', false);
            $('#book1').prop('checked', true);
            $('#book2').prop('checked', true);

            $("#uniform_m").prop("checked", true);

            $('#id_card').prop('checked', true);
            $('#id_lace').prop('checked', true);
        }

        $("#balance").val(balance);
    });

    var dtbl_search = $("#tbl_mdl_clients").DataTable({
        pageLength: 10,
        columnDefs: [
            {
                "targets": 0,
                "visible": false,
            },
        ],
        ajax: {
            url: "/learning-management/api/dtbl/mdl-pre-registered-clients-registration",
        }
    });

    $('#tbl_mdl_clients tbody').on( 'click', 'tr', function () {
        if ( $(this).hasClass('selected') ) {
            $(this).removeClass('selected');
        }
        else {
            dtbl_search.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }
    } );

    $('#btn_confirm').click( function () {
        var selected = dtbl_search.row('.selected').data();
        
        $.ajax({
            url: '/learning-management/api/clients/' + selected[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                if(response.data.status == "pre_registered" && response.data.is_oriented == false){
                    console.log(response.data);

                    $("#client_id").val(response.data.id);
                    $("#lname").val(response.data.lname);
                    $("#fname").val(response.data.fname);
                    $("#mname").val(response.data.mname);
                    $("#suffix").val(response.data.suffix);
                    $("#contact_number").val(response.data.contact_number);
                    $("#email").val(response.data.email);
                    $("#address").val(response.data.address);

                    var formattedDate = new Date(response.data.birth_date);
                    var d = ('0' + formattedDate.getDate()).slice(-2);
                    var m =  ('0' + (formattedDate.getMonth()+1)).slice(-2);
                    var y = formattedDate.getFullYear();

                    $("#birth_date").val(y + "-" + m + "-" + d);
            
                    $("#lname").prop('readonly', true);
                    $("#fname").prop('readonly', true);
                    $("#mname").prop('readonly', true);
                    $("#suffix").prop('readonly', true);
                    $("#contact_number").prop('readonly', true);
                    $("#birth_date").prop('readonly', true);
                    $("#address").prop('readonly', true);
                    $("#email").prop('readonly', true);

                } else if ((response.data.status == "pre_registered") && (response.data.is_oriented == true)){
                    $("#client_id").val(response.data.id);
                    $("#lname").val(response.data.lname);
                    $("#fname").val(response.data.fname);
                    $("#mname").val(response.data.mname);
                    $("#suffix").val(response.data.suffix);
                    $("#contact_number").val(response.data.contact_number);
                    $("#email").val(response.data.email);
                    $("#address").val(response.data.address);
                    $("#contact_person").val(response.data.contact_person);

                    var formattedDate = new Date(response.data.birth_date);
                    var d = ('0' + formattedDate.getDate()).slice(-2);
                    var m =  ('0' + (formattedDate.getMonth()+1)).slice(-2);
                    var y = formattedDate.getFullYear();

                    $("#birth_date").val(y + "-" + m + "-" + d);
            
                    $("#lname").prop('readonly', true);
                    $("#fname").prop('readonly', true);
                    $("#mname").prop('readonly', true);
                    $("#suffix").prop('readonly', true);
                    $("#contact_number").prop('readonly', true);
                    $("#birth_date").prop('readonly', true);
                    $("#address").prop('readonly', true);
                    $("#email").prop('readonly', true);
                    // $("#contact_person").prop('disabled', true);

                } else if((response.data.status == "oriented") && (response.data.is_oriented == true)){
                    $("#client_id").val(response.data.id);
                    $("#lname").val(response.data.lname);
                    $("#fname").val(response.data.fname);
                    $("#contact_number").val(response.data.contact_number);
                    $("#contact_person").val(response.data.contact_person);
                    $("#branch").val(response.data.branch);

                    $("#lname").prop('readonly', true);
                    $("#fname").prop('readonly', true);
                    $("#contact_number").prop('readonly', true);
                    $("#contact_person").prop('disabled', true);
                    $("#branch").prop('disabled', true);
                }
                
                $('#batch_number').find('option').remove();

                if(response.data.batch_numbers.length > 0){
                    var newOption = $('<option value="">Choose...</option>');
                    $('#batch_number').append(newOption);
                    
                    for(i=0; i < response.data.batch_numbers.length; i++){
                        var newOption = $(`<option value="${response.data.batch_numbers[i].id}">${response.data.batch_numbers[i].number}</option>`);
                        $('#batch_number').append(newOption);
                    }
                } else {
                    var newOption = $('<option value="">No Batch Numbers yet</option>');
                    $('#batch_number').append(newOption);
                }
            }
        });
    });

    $('#btn_clear_entries').click( function () {
        $("#client_id").val('');
        $("#lname").val('');
        $("#fname").val('');
        $("#mname").val('');
        $("#suffix").val('');
        $("#contact_number").val('');
        $("#birth_date").val('');
        $("#email").val('');
        $("#address").val('');
        $("#contact_person").val('');

        $("#lname").prop('readonly', false);
        $("#fname").prop('readonly', false);
        $("#mname").prop('readonly', false);
        $("#suffix").prop('readonly', false);
        $("#contact_number").prop('readonly', false);
        $("#birth_date").prop('readonly', false);
        $("#email").prop('readonly', false);
        $("#address").prop('readonly', false);
        $("#contact_person").prop('disabled', false);
    });

    // $('#branch').change(function() {
    //     $.ajax({
    //         url: '/learning-management/api/get-batch-numbers/' + $("#branch").val(),
    //         type: "GET",
    //         contentType: "application/json; charset=utf-8",
    //         success: function(response) {
    //             var newOption = $('<option value=""></option>');
    //             $('#batch_number').append(newOption);

    //             if(response.data.length > 0){
    //                 var newOption = $('<option value="'+val+'">'+val+'</option>');
    //                 $('#batch_number').append(newOption);
    //             }
    //         }
    //     });
    //   });
});
