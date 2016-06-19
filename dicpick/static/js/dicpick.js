$(function() {
  $('.with-select2 select').select2();

  $('.dateinput').datepicker({
    format: 'mm/dd/yyyy',
    assumeNearbyYear: true,
    autoclose: true
  });

  $(function () {
    $('[data-toggle="tooltip"]').tooltip()
  })
});
