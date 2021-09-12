$(document).ready(function(){

    var dtbl_system_logs = $('#index_table').DataTable({
        "dom": 'rtip',
        "pageLength": 20,
        "order": [[1, 'asc']],
        "processing": true,
        "serverSide": true,
        "autoWidth": false,
        "ordering": false,
        "columnDefs": [
            { "visible": false, "targets": 0 },
        ],
        "ajax": {
            "url": "/admin/dtbl/system-logs",
        }
    });
});
