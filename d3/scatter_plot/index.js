
const svg = d3.select('svg');
svg.style('background-color', 'white');

const svg_height = parseFloat(svg.attr('height'));
const svg_width = parseFloat(svg.attr('width'));

// @hack to work around “URL scheme must be ”http“ or ”https“ for CORS request.”
const data_location = "https://raw.githubusercontent.com/paul-tqh-nguyen/one_off_code/b93f123048a5b0797512ee5fad3c962ba0c3b0d7/d3/bar_chart/location_populations.json"; 

const render = data => {
    const getDatumPopulation = datum => datum.population;
    const getDatumLocation = datum => datum.location;
    const margin = {
        top: 80,
        bottom: 80,
        left: 120,
        right: 30,
    };
    
    const innerWidth = svg_width - margin.left - margin.right;
    const innerHeight = svg_height - margin.top - margin.bottom;
    
    const xScale = d3.scaleLinear()
          .domain([0, d3.max(data, getDatumPopulation)])
          .range([0, innerWidth])
          .nice();
    
    const yScale = d3.scalePoint()
          .domain(data.map(getDatumLocation))
          .range([0, innerHeight])
          .padding(0.5);
    
    const barChartGroup = svg.append('g')
          .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const barChartTitle = barChartGroup.append('text')
          .attr('class', 'chart-title')
          .text("Some Populous Countries")
          .attr('x', innerWidth * 0.3)
          .attr('y', -10);
    
    const yAxis = d3.axisLeft(yScale)
          .tickSize(-innerWidth);
    const yAxisGroup = barChartGroup.append('g')
          .call(yAxis);
    yAxisGroup.selectAll('.domain').remove();
    
    const xAxisTickFormat = number => d3.format('.3s')(number).replace(/G/,"B");
    const xAxis = d3.axisBottom(xScale)
          .tickFormat(xAxisTickFormat)
          .tickSize(-innerHeight);
    const xAxisGroup = barChartGroup.append('g')
          .call(xAxis)
          .attr('transform', `translate(0, ${innerHeight})`);
    xAxisGroup.selectAll('.domain').remove(); // remove ticks
    xAxisGroup.append('text') // X-axis label
        .attr('class','axis-label')
        .attr('fill', 'black')
        .attr('y', margin.bottom * 0.75)
        .attr('x', innerWidth / 2)
        .text('Population');

    // display data
    barChartGroup.selectAll('rect').data(data)
        .enter()
        .append('circle')
        .attr('cx', datum => xScale(getDatumPopulation(datum)))
        .attr('cy', datum => yScale(getDatumLocation(datum)))
        .attr('r', 20);

};

d3.json(data_location)
    .then(data => {
        data = data.map(datum => {
            return {
                population: parseFloat(datum.PopTotal) * 1000,
                location: datum.Location,
            };
        });
        render(data);
    }).catch(err => {
        console.error(err);
        return;
    });