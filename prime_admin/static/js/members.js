$(document).ready(function(){

    var CLIENTID;
    var ISLOADING = false;

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
            }
        }
    });

    // Command: toastr["success"](" ", "Saved Successfully!")

    toastr.options = {
    "closeButton": true,
    "debug": false,
    "newestOnTop": false,
    "progressBar": false,
    "positionClass": "toast-top-center",
    "preventDuplicates": false,
    "onclick": null,
    "showDuration": "3000",
    "hideDuration": "1000",
    "timeOut": "5000",
    "extendedTimeOut": "1000",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
    }

    var columnDefs;

    if(ROLE == "Marketer"){
        columnDefs = [
            { "visible": false, "targets": 0},
            { "visible": false, "targets": 8},
            { "visible": false, "targets": 15},
            { "width": 100, "targets": 15},
            { "width": "10px", "targets": 12}
        ];
    } else {
        columnDefs = [
            { "visible": false, "targets": 0},
            { "width": 100, "targets": 15},
            { "width": "10px", "targets": 12}
        ];
    }

    var savedValues = {
        'book_none': false,
        'book1': false,
        'book2': false,
        'uniform_xs': false,
        'uniform_s': false,
        'uniform_m': false,
        'uniform_l': false,
        'uniform_xl': false,
        'uniform_xxl': false,
        'uniform_none': false,
        'id_card': false,
        'id_lace': false,
    }

    var table = $('#tbl_members').DataTable({
        "dom": 'rtip',
        "pageLength": 20,
        "order": [[ 1, 'asc' ]],
        "processing": true,
        "serverSide": true,
        "autoWidth": false,
        "columnDefs": columnDefs,
        "ordering": false,
        "ajax": {
            "url": "/learning-management/dtbl/members",
            "data": function (d) {
                d.branch = $("#branch").val();
                d.batch_no = $("#batch_no").val();
                d.schedule = $("#schedule").val();
                d.date_from = $("#date_from").val();
                d.date_to = $("#date_to").val();
            },
            "dataSrc": function(json){
                $("#total_installment").html("₱" + json.totalInstallment);
                $("#total_full_payment").html("₱" + json.totalFullPayment);
                $("#total_premium_payment").html("₱" + json.totalPremiumPayment);
                $("#total_payment").html("₱" + json.totalPayment);
                $("#sales_today").html("₱" + json.salesToday);

                return json.data;
            }
        },
        "createdRow": function(row, data, dataIndex){
            if(data[11] == "No"){
                $(row).addClass('row-not-deposit');
            }

            if(data[10] == "NOT PAID"){
                $(row).addClass('row-not-paid');
            }
        }
    });

    // $('#tbl_members tbody').on('click', 'tr', function () {
    //     var data = table.row( this ).data();
        
    //     $("#viewModal").modal('toogle');
    //     $("#viewModal").modal('show');
    // } );

    $('#tbl_members tbody').on('click', '.btn-upgrade', function () {
        var data = table.row( $(this).parents('tr')).data();
        
        $.ajax({
            url: '/learning-management/api/members/' + data[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                CLIENTID = response.data.id;

                $("#upgrade_client_id").val(response.data.id);
                $("#upgrade_last_name").val(response.data.lname);
                $("#upgrade_first_name").val(response.data.fname);
                $("#upgrade_middle_name").val(response.data.mname);
                $("#upgrade_suffix").val(response.data.suffix);
                $("#upgrade_mode_of_payment").val(response.data.mode_of_payment.toUpperCase());
                $("#upgrade_amount").val(response.data.amount);
                $("#upgrade_balance").val(response.data.balance);

                $("#tbl_upgrade_payment_history > tbody").empty();

                for(i=0; i < response.data.payments.length; i++){
                    $('#tbl_upgrade_payment_history > tbody:first').append(
                        `<tr>
                        <td class="text-center">${response.data.payments[i].amount}</td>
                        <td class="text-center">${response.data.payments[i].current_balance}</td>
                        <td class="text-center">${response.data.payments[i].date}</td>
                        <td class="text-center">${response.data.payments[i].remarks}</td>
                        <td class="text-center">${response.data.payments[i].deposited}</td>
                        </tr>`
                        );
                }

                console.log(response.data);
                $('#upgrade_book_none').prop('checked', false);
                $('#upgrade_book1').prop('checked', false);
                $('#upgrade_book2').prop('checked', false);

                if(response.data.books.book_none){
                    $('#upgrade_book_none').prop('checked', true);
                    savedValues.book_none = true;
                } else if(response.data.books.volume1){
                    $('#upgrade_book1').prop('checked', true);
                    savedValues.book1 = true;
                } else if(response.data.books.volume2){
                    $('#upgrade_book2').prop('checked', true);
                    savedValues.book2 = true;
                }

                if(response.data.uniforms.uniform_none){
                   $("#upgrade_uniform_none").prop("checked", true);
                   savedValues.uniform_none = true;
                } else if(response.data.uniforms.uniform_xs){
                    $("#upgrade_uniform_xs").prop("checked", true);
                    savedValues.uniform_xs = true;
                } else if(response.data.uniforms.uniform_s){
                    $("#upgrade_uniform_s").prop("checked", true);
                    savedValues.uniform_s = true;
                } else if(response.data.uniforms.uniform_m){
                    $("#upgrade_uniform_m").prop("checked", true);
                    savedValues.uniform_m = true;
                } else if(response.data.uniforms.uniform_l){
                    $("#upgrade_uniform_l").prop("checked", true);
                    savedValues.uniform_l = true;
                } else if(response.data.uniforms.uniform_xl){
                    $("#upgrade_uniform_xl").prop("checked", true);
                    savedValues.uniform_xl = true;
                } else if(response.data.uniforms.uniform_xxl){
                    $("#upgrade_uniform_xxl").prop("checked", true);
                    savedValues.uniform_xxl = true;
                }
            }
        });
    } );

    $('#tbl_members tbody').on('click', '.btn-edit', function () {
        var data = table.row( $(this).parents('tr')).data();
        
        $.ajax({
            url: '/learning-management/api/members/' + data[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                CLIENTID = response.data.id;

                $("#edit_client_id").val(response.data.id);
                $("#edit_last_name").val(response.data.lname);
                $("#edit_first_name").val(response.data.fname);
                $("#edit_middle_name").val(response.data.mname);
                $("#edit_suffix").val(response.data.suffix);
                $("#edit_mode_of_payment").val(response.data.mode_of_payment.toUpperCase());
                $("#edit_amount").val(response.data.amount);
                $("#edit_balance").val(response.data.balance);

                $("#tbl_edit_payment_history > tbody").empty();

                for(i=0; i < response.data.payments.length; i++){
                    $('#tbl_edit_payment_history > tbody:first').append(
                        `<tr>
                        <td class="text-center">${response.data.payments[i].amount}</td>
                        <td class="text-center">${response.data.payments[i].current_balance}</td>
                        <td class="text-center">${response.data.payments[i].date}</td>
                        <td class="text-center">${response.data.payments[i].remarks}</td>
                        <td class="text-center">${response.data.payments[i].deposited}</td>
                        </tr>`
                        );
                }

                console.log(response.data);
                $('#book_none').prop('checked', false);
                $('#book1').prop('checked', false);
                $('#book2').prop('checked', false);

                if(response.data.books.book_none){
                    $('#book_none').prop('checked', true);
                } else if(response.data.books.volume1){
                    $('#book1').prop('checked', true);
                } else if(response.data.books.volume2){
                    $('#book2').prop('checked', true);
                }

                if(response.data.uniforms.uniform_none){
                   $("#uniform_none").prop("checked", true);
                } else if(response.data.uniforms.uniform_xs){
                    $("#uniform_xs").prop("checked", true);
                } else if(response.data.uniforms.uniform_s){
                    $("#uniform_s").prop("checked", true);
                } else if(response.data.uniforms.uniform_m){
                    $("#uniform_m").prop("checked", true);
                } else if(response.data.uniforms.uniform_l){
                    $("#uniform_l").prop("checked", true);
                } else if(response.data.uniforms.uniform_xl){
                    $("#uniform_xl").prop("checked", true);
                } else if(response.data.uniforms.uniform_xxl){
                    $("#uniform_xxl").prop("checked", true);
                }
            }
        });
    } );
        
    $('#tbl_members tbody').on('click', '.btn-view', function () {
        var data = table.row( $(this).parents('tr') ).data();
        
        $.ajax({
            url: '/learning-management/api/members/' + data[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                CLIENTID = response.data.id;

                $("#client_id").val(response.data.id);
                $("#view_last_name").val(response.data.lname);
                $("#view_first_name").val(response.data.fname);
                $("#view_middle_name").val(response.data.mname);
                $("#view_suffix").val(response.data.suffix);
                $("#view_batch_no").val(response.data.batch_no);
                $("#view_schedule").val(response.data.schedule);
                $("#view_branch").val(response.data.branch);
                $("#view_contact_person").val(response.data.contact_person);
                $("#view_date_of_birth").val(response.data.birth_date);
                $("#view_passport").val(response.data.passport);
                $("#view_contact_no").val(response.data.contact_no);
                $("#view_email").val(response.data.email);
                $("#view_address").val(response.data.address);
                $("#view_e_registration").val(response.data.e_registration);
                $("#view_mode_of_payment").val(response.data.mode_of_payment.toUpperCase());
                $("#view_book").val(response.data.book);
                $("#view_uniform").val(response.data.uniform);
                $("#view_id_materials").val(response.data.id_materials);
                $("#view_amount").val(response.data.amount);
                $("#view_balance").val(response.data.balance);

                $("#tbl_payment_history > tbody").empty();

                for(i=0; i < response.data.payments.length; i++){
                    $('#tbl_payment_history > tbody:first').append(
                        `<tr>
                        <td class="text-center">${response.data.payments[i].amount}</td>
                        <td class="text-center">${response.data.payments[i].current_balance}</td>
                        <td class="text-center">${response.data.payments[i].date}</td>
                        <td class="text-center">${response.data.payments[i].remarks}</td>
                        <td class="text-center">${response.data.payments[i].deposited}</td>
                        </tr>`
                        );
                }
            }
        });

    } );

    $("#btn_edit").click(function(){
        if($(this).html() == "Edit"){
            $(this).html("Save");
            $("#view_last_name").prop('disabled', false);
            $("#view_first_name").prop('disabled', false);
            $("#view_middle_name").prop('disabled', false);
            $("#view_suffix").prop('disabled', false);
            // $("#view_schedule").prop('disabled', false);
            // $("#view_date_of_birth").prop('disabled', false);
            $("#view_passport").prop('disabled', false);
            $("#view_contact_no").prop('disabled', false);
            $("#view_email").prop('disabled', false);
            $("#view_address").prop('disabled', false);
            $("#view_e_registration").prop('disabled', false);
        }else if ($(this).html() == "Save"){
            $(this).html("Edit");
            $("#view_last_name").prop('disabled', true);
            $("#view_first_name").prop('disabled', true);
            $("#view_middle_name").prop('disabled', true);
            $("#view_suffix").prop('disabled', true);
            // $("#view_schedule").prop('disabled', true);
            // $("#view_date_of_birth").prop('disabled', true);
            $("#view_passport").prop('disabled', true);
            $("#view_contact_no").prop('disabled', true);
            $("#view_email").prop('disabled', true);
            $("#view_address").prop('disabled', true);
            $("#view_e_registration").prop('disabled', true);

            var lname = $("#view_last_name").val();
            var fname = $("#view_first_name").val();
            var mname = $("#view_middle_name").val();
            var suffix = $("#view_suffix").val();
            var birth_date = $("#view_date_of_birth").val();
            var passport = $("#view_passport").val();
            var contact_no = $("#view_contact_no").val();
            var email = $("#view_email").val();
            var address = $("#view_address").val();
            var e_registration = $("#view_e_registration").val();

            $.ajax({
                url: "/learning-management/api/members/" + $("#client_id").val() + "/edit",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    "lname": lname,
                    "fname": fname,
                    "mname": mname,
                    "suffix": suffix,
                    "birth_date": birth_date,
                    "passport": passport,
                    "contact_no": contact_no,
                    "email": email,
                    "address": address,
                    "e_registration": e_registration
                }),
                contentType: "application/json; charset=utf-8",
                success: function(response){
                    if(response.result){
                        table.ajax.reload();
                        toastr.success("Saved Successfully!");
                    }else{
                        toastr.error("Error Occured!, Saving Failed");
                    }
                }
            });
        }
    });


    $("#book1").click(function(){
        $('#book_none').prop('checked', false);
    });

    $("#book2").click(function(){
        $('#book_none').prop('checked', false);
    });

    $("#book_none").click(function(){
        $('#book1').prop('checked', false);
        $('#book2').prop('checked', false);
    });

    $("#btn_print").click(function(){
        var branch = $("#branch").val();
        var batch_no = $("#batch_no").val();
        var schedule = $("#schedule").val();
        window.open(PDF_URL + `?branch=${branch}&batch_no=${batch_no}&schedule=${schedule}`);
    });

    $("#btn_print_audit").click(function(){
        var branch = $("#branch").val();
        var batch_no = $("#batch_no").val();
        var schedule = $("#schedule").val();
        window.open(STUDENTS_AUDIT_PDF_URL + `?branch=${branch}&batch_no=${batch_no}&schedule=${schedule}&report=audit`);
    });

    $("#btn_print_student_info").click(function(){
        window.open(STUDENT_INFO_PDF_URL + `?student_id=${CLIENTID}`,'_blank');
    });

    $("#btn_search").click(function(){
        table.search($("#search_input").val()).draw();
    });

    $("#btn_clear_entry").click(function(){
        $("#search_input").val("")
        table.search("").draw();    
    });

    $("#chkbox_upgrade_full_payment").click(function(){
        if(ISLOADING){
            $("#chkbox_upgrade_full_payment").attr('onclick', "return false;");
            return;
        }

        $('#chkbox_upgrade').prop('checked', false); // Unchecks it

        var is_checked = $(this).is(":checked");

        if(is_checked){
            ISLOADING = true;

            $.ajax({
                url: '/learning-management/api/members/' + CLIENTID,
                type: "GET",
                contentType: "application/json; charset=utf-8",
                success: function(response) {
                    var new_amount = parseInt(response.data.balance) - 800;

                    $("#new_amount").val(new_amount);
                    $("#new_amount").prop('readonly', true);
                    $('#book_none').prop('checked', false);
                    $('#book1').prop('checked', true);
                    $('#book2').prop('checked', false);

                    $("#uniform_m").prop("checked", true);

                    $('#id_card').prop('checked', false);
                    $('#id_lace').prop('checked', false);

                    $("#id_lace").attr('onclick', "return false;");
                    $("#id_card").attr('onclick', "return false;");
                    $("#book_none").attr('onclick', "return false;");
                    $("#book1").attr('onclick', "return false;");
                    $("#book2").attr('onclick', "return false;");
                    
                    ISLOADING = false;
                    $("#chkbox_upgrade_full_payment").attr('onclick', "");
                }
            });

            return;
        }

        $("#new_amount").val('');
        $("#new_amount").prop('readonly', false);
        $('#book_none').prop('checked', true);
        $('#book1').prop('checked', false);
        $('#book2').prop('checked', false);

        $("#uniform_m").prop("checked", false);
        $("#uniform_none").prop("checked", true);

        $('#id_card').prop('checked', false);
        $('#id_lace').prop('checked', false);

        $("#id_lace").attr('onclick', "");
        $("#id_card").attr('onclick', "");
        $("#book_none").attr('onclick', "");
        $("#book1").attr('onclick', "");
        $("#book2").attr('onclick', "");
    });


    $("#chkbox_upgrade").click(function(){
        if(ISLOADING){
            $("#chkbox_upgrade").attr('onclick', "return false;");
            return;
        }

        $('#chkbox_upgrade_full_payment').prop('checked', false); // Unchecks it

        var is_checked = $(this).is(":checked");

        if(is_checked){
            ISLOADING = true;

            $.ajax({
                url: '/learning-management/api/members/' + CLIENTID,
                type: "GET",
                contentType: "application/json; charset=utf-8",
                success: function(response) {
                    var new_amount = parseInt(response.data.balance) + 700;

                    $("#new_amount").val(new_amount);
                    $("#new_amount").prop('readonly', true);
                    $('#book_none').prop('checked', false);
                    $('#book1').prop('checked', true);
                    $('#book2').prop('checked', true);

                    $("#uniform_m").prop("checked", true);

                    $('#id_card').prop('checked', true);
                    $('#id_lace').prop('checked', true);

                    $("#id_lace").attr('onclick', "return false;");
                    $("#id_card").attr('onclick', "return false;");
                    $("#book_none").attr('onclick', "return false;");
                    $("#book1").attr('onclick', "return false;");
                    $("#book2").attr('onclick', "return false;");
                    
                    ISLOADING = false;
                    $("#chkbox_upgrade").attr('onclick', "");
                }
            });

            return;
        }

        $("#new_amount").val('');
        $("#new_amount").prop('readonly', false);
        $('#book_none').prop('checked', true);
        $('#book1').prop('checked', false);
        $('#book2').prop('checked', false);

        $("#uniform_m").prop("checked", false);
        $("#uniform_none").prop("checked", true);

        $('#id_card').prop('checked', false);
        $('#id_lace').prop('checked', false);

        $("#id_lace").attr('onclick', "");
        $("#id_card").attr('onclick', "");
        $("#book_none").attr('onclick', "");
        $("#book1").attr('onclick', "");
        $("#book2").attr('onclick', "");
    });


    $("#upgrade_chkbox_upgrade").click(function(){
        if(ISLOADING){
            $("#upgrade_chkbox_upgrade").attr('onclick', "return false;");
            return;
        }

        var is_checked = $(this).is(":checked");

        if(is_checked){
            ISLOADING = true;

            $("#btn_confirm_upgrade").prop('disabled', false);

            $.ajax({
                url: '/learning-management/api/members/' + CLIENTID,
                type: "GET",
                contentType: "application/json; charset=utf-8",
                success: function(response) {
                    if (response.data.mode_of_payment == "full_payment" || response.data.mode_of_payment == "full_payment_promo"){
                        var new_amount = 1500;

                        $("#upgrade_new_amount").val(new_amount);
                        $('#upgrade_book_none').prop('checked', false);
                        $('#upgrade_book1').prop('checked', true);
                        $('#upgrade_book2').prop('checked', true);
    
                        $('#upgrade_id_card').prop('checked', true);
                        $('#upgrade_id_lace').prop('checked', true);
    
                        $("#upgrade_id_lace").attr('onclick', "return false;");
                        $("#upgrade_id_card").attr('onclick', "return false;");
                        $("#upgrade_book_none").attr('onclick', "return false;");
                        $("#upgrade_book1").attr('onclick', "return false;");
                        $("#upgrade_book2").attr('onclick', "return false;");
                    } else {
                        var new_amount = parseInt(response.data.balance) + 700;

                        $("#upgrade_new_amount").val(new_amount);
                        $('#upgrade_book_none').prop('checked', false);
                        $('#upgrade_book1').prop('checked', true);
                        $('#upgrade_book2').prop('checked', true);
    
                        $("#upgrade_uniform_m").prop("checked", true);
    
                        $('#upgrade_id_card').prop('checked', true);
                        $('#upgrade_id_lace').prop('checked', true);
    
                        $("#upgrade_id_lace").attr('onclick', "return false;");
                        $("#upgrade_id_card").attr('onclick', "return false;");
                        $("#upgrade_book_none").attr('onclick', "return false;");
                        $("#upgrade_book1").attr('onclick', "return false;");
                        $("#upgrade_book2").attr('onclick', "return false;");
                    }
                    
                    ISLOADING = false;
                    $("#upgrade_chkbox_upgrade").attr('onclick', "");
                }
            });

            return;
        }

        $("#upgrade_new_amount").val('');

        $("#btn_confirm_upgrade").prop('disabled', true);

        if(savedValues.book_none){
            $('#upgrade_book_none').prop('checked', true);
        } else {
            $('#upgrade_book_none').prop('checked', false);
        }
        
        if(savedValues.book1){
            $('#upgrade_book1').prop('checked', true);
        } else{
            $('#upgrade_book1').prop('checked', false);
        }
        
        if(savedValues.book2){
            $('#upgrade_book2').prop('checked', true);
        } else {
            $('#upgrade_book2').prop('checked', false);
        }

        if(savedValues.uniform_none){
            $("#upgrade_uniform_none").prop("checked", true);
        } else{
            $("#upgrade_uniform_none").prop("checked", false);
        }

        if(savedValues.uniform_m){
            $("#upgrade_uniform_m").prop("checked", true);
        } else{
            $("#upgrade_uniform_m").prop("checked", false);
        }

        if(savedValues.uniform_xs){
            $("#upgrade_uniform_xs").prop("checked", true);
        } else{
            $("#upgrade_uniform_xs").prop("checked", false);
        }

        if(savedValues.uniform_s){
            $("#upgrade_uniform_s").prop("checked", true);
        } else{
            $("#upgrade_uniform_s").prop("checked", false);
        }

        if(savedValues.uniform_m){
            $("#upgrade_uniform_m").prop("checked", true);
        } else{
            $("#upgrade_uniform_m").prop("checked", false);
        }

        if(savedValues.uniform_l){
            $("#upgrade_uniform_l").prop("checked", true);
        } else{
            $("#upgrade_uniform_l").prop("checked", false);
        }

        if(savedValues.uniform_xl){
            $("#upgrade_uniform_xl").prop("checked", true);
        } else{
            $("#upgrade_uniform_xl").prop("checked", false);
        }

        if(savedValues.uniform_xxl){
            $("#upgrade_uniform_xxl").prop("checked", true);
        } else{
            $("#upgrade_uniform_xxl").prop("checked", false);
        }

        $('#upgrade_id_card').prop('checked', false);
        $('#upgrade_id_lace').prop('checked', false);

        $("#upgrade_id_lace").attr('onclick', "");
        $("#upgrade_id_card").attr('onclick', "");
        $("#upgrade_book_none").attr('onclick', "");
        $("#upgrade_book1").attr('onclick', "");
        $("#upgrade_book2").attr('onclick', "");
    });

    $("#book_none").click(function(){
        var is_checked = $("#chkbox_upgrade").is(":checked");

        if(is_checked){
            $('#book_none').prop('checked', false);
            $('#book1').prop('checked', true);
            $('#book2').prop('checked', true);
        }
    });

    $("#branch").change(function(){
        BRANCH = $(this).val();

        $.ajax({
        url: `/learning-management/api/branches/${BRANCH}/batches`,
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                $('#batch_no').find('option').remove();

                
                if (BRANCH == 'all'){
                    var newOption = $('<option value="all">Please select branch first</option>');
                    $('#batch_no').append(newOption);
                    $('#batch_no').val('all');
                    table.ajax.reload();
                    return;
                }
                
                if (response.data.length > 0) {
                    var newOption = $('<option value="all">All</option>');
                    $('#batch_no').append(newOption);

                    for (i = 0; i < response.data.length; i++) {
                        var newOption = $(`<option value="${response.data[i].id}">${response.data[i].number}</option>`);
                        $('#batch_no').append(newOption);
                    }
                } else {
                    var newOption = $('<option value="all">No batch number available</option>');
                    $('#batch_no').append(newOption);
                }


                $('#batch_no').val('all');
        
                table.ajax.reload();
            }
        });
    });

    $("#batch_no").change(function(){
        BATCH_NO = $(this).val();
        table.ajax.reload();
    });

    $("#schedule").change(function(){
        SCHEDULE = $(this).val();
        table.ajax.reload();
    });

    $('#date_from').change(function() {
        table.ajax.reload();
    });

    $('#date_to').change(function() {
        table.ajax.reload();
    });
});
