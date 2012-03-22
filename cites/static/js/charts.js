(function ($, app) {
    var array_move = function (data, old_index, new_index) {
        if (new_index >= data.length) {
            var k = new_index - data.length;
            while ((k--) + 1) { data.push(undefined); }
        }

        data.splice(new_index, 0, data.splice(old_index, 1)[0]);
        return data;
    };

    function bar_chart(data, labels) {
        var chart = d3.select("#bar-chart");

        var div = chart.selectAll("div").data(data).enter();
        var progress = div.append("div")
                          .style("width", "100%")
                          .attr("class", "progress");
        progress.append("div")
                .attr("class", "bar")
                .style("width", function(d) { return d  + "%"; })
                .append("span").attr("class", function(d, i) {
                    var cls = "value "
                    if(d === 0) { cls = cls + "value-null"; }
                    if(d >= 10) {cls += "value-double-digits"}
                    return cls;
                })
                .text(function(d) { return d; })
        progress.append("div")
                .attr("class", "title")
                .text(function(d, i) { return labels[i] });

        var x = d3.scale.linear()
                  .domain([0, d3.max(data)])
                  .range(["0px", "420px"]);
    };

    function pie_chart(data) {
        var data = $.grep(data, function (n) {
            if(n > 0) return n;
        });

        // first big values should be on top of the circle
        data = array_move(data, 1, data.length - 1);

        var w = 300,
            h = 300,
            r = Math.min(w, h) / 2,
            color = d3.scale.category20(),
            donut = d3.layout.pie(),
            arc = d3.svg.arc().innerRadius(0).outerRadius(r);

        // disable sort
        donut.sort(null);

        var vis = d3.select("#pie-chart")
                    .append("svg")
                    .data([data])
                    .attr("width", w)
                    .attr("height", h);

        var arcs = vis.selectAll("g.arc")
                      .data(donut)
                      .enter().append("g")
                      .attr("class", "arc")
                      .attr("transform", "translate(" + r + "," + r + ")");

        arcs.append("path")
            .attr("fill", function(d, i) { return color(i); })
            .attr("d", arc);

        arcs.append("text")
            .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
            .attr("dy", "0px")
            .attr("text-anchor", "middle")
            .attr("display", function(d) { return d.value > 2 ? null : "none"; })
            .text(function(d, i) { return d.value; });

        pie_chart_lengend_color(color);
    };

    function pie_chart_lengend_color(color) {
        var legends = $(".legend").children("li");
        $.each(legends, function (i) {
            if (i > 1) {
                i = i - 1;
            }
            if(i == 1) {
                i = legends.length - 1;
            }
            $(this).find(".color").css("background", color(i));
        });
    };

    $(function () {
        bar_chart(app.chart_data, app.chart_labels);
        pie_chart(app.chart_data);
    });
})($, app)
