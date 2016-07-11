$(function() {
  // Initialize the assignees select box.

  var pathParts = window.location.pathname.split('/');
  var eventPathPrefix = pathParts[1] + '/' + pathParts[2];  // pathParts[0] is expected to be an empty string.
  var autocompleteUrl = eventPathPrefix + '/participants/autocomplete/';

  $('.with-select2 select.field-assignees').each(function() {
    var numPeople = parseInt($(this).closest('tr').find('input.field-num_people').val());
    $(this).select2({
      ajax: {
        url: autocompleteUrl,
        dataType: 'json',
        delay: 250,
        cache: true,
        data: function(params) {
          return {
            q: params.term,
            d: $(this).attr('dp-for-date'),
            t: $(this).attr('dp-for-tags')
          };
        }
      },
      escapeMarkup: function (markup) { return markup; },  // Allow markup in our template.
      templateResult: function(item) {
        function classForProp(prop) {
          return item[prop] ? ' ' + prop.replace(/_/g, '-') : '';
        }
        return '<div class="assignee-option' +
                            classForProp('disqualified_for_date') +
                            classForProp('disqualified_for_tags') + '"' +
                  (item.tooltip ? ('data-toggle="tooltip" title="' + item.tooltip + '"') : '') +
               '>' + item.text + '</div>';
      },
      minimumInputLength: 2,
      maximumSelectionLength: numPeople
    });
  });

  // Initialize other select boxes.

  $('.with-select2 select').not('select.field-assignees').select2();

  // Initialize date fields.

  $('.dateinput').datepicker({
    format: 'mm/dd/yyyy',
    assumeNearbyYear: true,
    autoclose: true
  });

  // Initialize tooltips.

  $(function() {
    $('[data-toggle="tooltip"]').tooltip()
  });
});
