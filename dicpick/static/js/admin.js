var dicpick = dicpick || {};
dicpick.admin = dicpick.admin || {};

dicpick.admin.init = function() {
  $('#camp-context-select').change(function(e) {
    // Reload the page with a new query.
    location.search = 'c=' + this.value;
  });

  $('a').click(function(e) {
    if (this.pathname.startsWith('/dpadmin')) {
      e.preventDefault();
      //console.log(this.href);
      location.href = this.href + '?c=' + $('#camp-context-select').val();
    }
  });
};

$(function() {
  dicpick.admin.init();
});

