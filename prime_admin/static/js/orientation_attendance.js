$(document).ready(function () {

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
            }
        }
    });


    var dtbl_members = $('#tbl_members').DataTable({
        "dom": 'rtip',
        "pageLength": 20,
        "order": [[1, 'asc']],
        "processing": true,
        "serverSide": true,
        "autoWidth": false,
        "columnDefs": [
            { "visible": false, "targets": 0 },
        ],
        "ajax": {
            "url": "/learning-management/dtbl/orientation-attendance-members",
            "data": function (d) {
                d.branch = $("#branch_filter").val();
                d.contact_person = $("#contact_person_filter").val();
            },
        }
    });

    $("#branch_filter").change(function () {
        dtbl_members.ajax.reload();
    });

    $("#contact_person_filter").change(function () {
        dtbl_members.ajax.reload();
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
            url: "/learning-management/api/dtbl/mdl-pre-registered-clients",
        }
    });

    $('#tbl_mdl_clients tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
        }
        else {
            dtbl_search.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }
    });


    $('#btn_confirm').click(function () {
        var selected = dtbl_search.row('.selected').data();

        $.ajax({
            url: '/learning-management/api/clients/' + selected[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function (response) {
                console.log(response.data);

                $("#client_id").val(selected[0]);
                $("#lname").val(selected[1]);
                $("#fname").val(selected[2]);
                $("#contact_no").val(selected[5]);
                $("#contact_person").val(response.data.contact_person);

                $("#lname").prop('readonly', true);
                $("#fname").prop('readonly', true);
                $("#contact_no").prop('readonly', true);

                if (response.data.status != "pre_registered") {
                    $("#contact_person").prop('disabled', true);
                }
            }
        });
    });

    $('#btn_clear_entries').click(function () {
        $("#client_id").val('');
        $("#lname").val('');
        $("#fname").val('');
        $("#contact_no").val('');
        $("#contact_person").val('');
        $("#referred_by").val('');
        $("#referred_by_name").val('');

        $("#lname").prop('readonly', false);
        $("#fname").prop('readonly', false);
        $("#contact_no").prop('readonly', false);
        $("#contact_person").prop('disabled', false);
    });

    var dtbl_search_refferal = $("#tbl_mdl_referrals").DataTable({
        pageLength: 10,
        columnDefs: [
            {
                "targets": 0,
                "visible": false,
            },
        ],
        ajax: {
            url: "/learning-management/api/dtbl/mdl-referrals",
        }
    });

    load();

    $('#tbl_mdl_referrals tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
        }
        else {
            dtbl_search_refferal.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }
    });

    $('#btn_confirm_referral').click(function () {
        var selected = dtbl_search_refferal.row('.selected').data();

        $.ajax({
            url: '/learning-management/api/clients/' + selected[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function (response) {
                $("#referred_by").val(response.data.id);
                var full_name = response.data.fname + " " + response.data.lname;
                $("#referred_by_name").val(full_name);
                $("#contact_person").val(response.data.contact_person);
                $("#contact_person").prop('disabled', true);
            }
        });
    });

    function load() {
        $.ajax({
            url: '/learning-management/api/get-branch-contact-persons/' + $("#branch").val(),
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function (response) {
                $('#contact_person').find('option').remove();

                if (response.data.length > 0) {
                    var newOption = $('<option value="">Choose...</option>');
                    $('#contact_person').append(newOption);

                    for (i = 0; i < response.data.length; i++) {
                        var newOption = $(`<option value="${response.data[i].id}">${response.data[i].fname}</option>`);
                        $('#contact_person').append(newOption);
                    }
                } else {
                    var newOption = $('<option value="">No Contact Persons available</option>');
                    $('#contact_person').append(newOption);
                }
            }
        });
    }


    $('#branch').change(function () {
        $.ajax({
            url: '/learning-management/api/get-branch-contact-persons/' + $("#branch").val(),
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function (response) {
                $('#contact_person').find('option').remove();

                if (response.data.length > 0) {
                    var newOption = $('<option value="">Choose...</option>');
                    $('#contact_person').append(newOption);

                    for (i = 0; i < response.data.length; i++) {
                        var newOption = $(`<option value="${response.data[i].id}">${response.data[i].fname}</option>`);
                        $('#contact_person').append(newOption);
                    }
                } else {
                    var newOption = $('<option value="">No Contact Persons available</option>');
                    $('#contact_person').append(newOption);
                }
            }
        });
    });


    $('#tbl_members tbody').on('click', '.btn-view', function () {
        var data = dtbl_members.row($(this).parents('tr')).data();

        $.ajax({
            url: '/learning-management/api/members/' + data[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function (response) {
                CLIENTID = response.data.id;

                $("#view_client_id").val(response.data.id);
                $("#view_last_name").val(response.data.lname);
                $("#view_first_name").val(response.data.fname);
                $("#view_middle_name").val(response.data.mname);
                $("#view_suffix").val(response.data.suffix);
                $("#view_contact_no").val(response.data.contact_no);
                $("#view_branch").val(response.data.branch);
                $("#view_contact_person").val(response.data.contact_person);
            }
        });

    });

    $("#btn_edit").click(function(){
        if($(this).html() == "Edit"){
            $(this).html("Save");
            $("#view_last_name").prop('disabled', false);
            $("#view_first_name").prop('disabled', false);
            $("#view_middle_name").prop('disabled', false);
            $("#view_suffix").prop('disabled', false);
            $("#view_contact_no").prop('disabled', false);
        }else if ($(this).html() == "Save"){
            $(this).html("Edit");
            $("#view_last_name").prop('disabled', true);
            $("#view_first_name").prop('disabled', true);
            $("#view_middle_name").prop('disabled', true);
            $("#view_suffix").prop('disabled', true);
            $("#view_contact_no").prop('disabled', true);

            var lname = $("#view_last_name").val();
            var fname = $("#view_first_name").val();
            var mname = $("#view_middle_name").val();
            var suffix = $("#view_suffix").val();
            var contact_no = $("#view_contact_no").val();

            $.ajax({
                url: "/learning-management/api/members/" + $("#view_client_id").val() + "/edit",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    "lname": lname,
                    "fname": fname,
                    "mname": mname,
                    "suffix": suffix,
                    "contact_no": contact_no,
                    'from': 'orientation_attendance'
                }),
                contentType: "application/json; charset=utf-8",
                success: function(response){
                    if(response.result){
                        dtbl_members.ajax.reload();
                        toastr.success("Saved Successfully!");
                    }else{
                        toastr.error("Error Occured!, Saving Failed");
                    }
                }
            });
        }
    });

});