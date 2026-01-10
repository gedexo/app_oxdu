/* total-app chart*/
var options3 = {
  chart: {
      height: 170,
      width: 100,
      type: "radialBar",
  },

  series: [85],
  colors: ["rgba(51, 102, 255, 1)"],
  plotOptions: {
      radialBar: {
          hollow: {
              margin: 0,
              size: "45%",
          },
          dataLabels: {
              name: {
                  offsetY: -10,
                  color: "#4b9bfa",
                  fontSize: ".625rem",
                  show: false
              },
              value: {
                  offsetY: 8,
                  color: "#4b9bfa",
                  fontSize: "1.25rem",
                  show: true,
                  fontFamily: "Roboto",
                  fontWeight: 400
              }
          }
      }
  },
  states: {
  normal: {
    filter: {
      type: 'none',
    }
  },
  hover: {
    filter: {
      type: 'none',
    }
  },
  active: {
    filter: {
      type: 'none',
    }
  },
},
  grid: {
      padding: {
        bottom: -8,
        top: -15,
      },
  },
  stroke: {
      lineCap: "round"
  },
  labels: ["Status"]
};
document.querySelector("#total-app").innerHTML = " ";
var chart3 = new ApexCharts(document.querySelector("#total-app"), options3);
chart3.render();
function totalApp() {
  chart3.updateOptions({
      colors: ["rgba(" + myVarVal + ", 1)"],
  })
};
/* total-app chart*/

/* shortlist chart*/
var options = {
    chart: {
        height: 170,
        width: 100,
        type: "radialBar",
    },

    series: [60],
    colors: ["rgba(13, 205, 148, 1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "45%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: -10,
                    color: "#4b9bfa",
                    fontSize: ".625rem",
                    show: false
                },
                value: {
                    offsetY: 8,
                    color: "#4b9bfa",
                    fontSize: "1.25rem",
                    show: true,
                    fontFamily: "Roboto",
                    fontWeight: 400
                },
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["Status"]
};
document.querySelector("#shortlist").innerHTML = " ";
var chart = new ApexCharts(document.querySelector("#shortlist"), options);
chart.render();
/* shortlist chart*/
/* rejected chart*/
var options = {
    chart: {
        height: 170,
        width: 100,
        type: "radialBar",
    },

    series: [25],
    colors: ["rgba(247, 40, 74, 1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "45%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: -10,
                    color: "#4b9bfa",
                    fontSize: ".625rem",
                    show: false
                },
                value: {
                    offsetY: 8,
                    color: "#4b9bfa",
                    fontSize: "1.25rem",
                    show: true,
                    fontFamily: "Roboto",
                    fontWeight: 400
                },
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["Status"]
};
document.querySelector("#rejected").innerHTML = " ";
var chart = new ApexCharts(document.querySelector("#rejected"), options);
chart.render();
/* rejected chart*/


/* shares chart*/
var options2 = {
    chart: {
        height: 170,
        width: 100,
        type: "radialBar",
    },

    series: [67],
    colors: ["rgba(51, 102, 255, 1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "45%",
            },
            dataLabels: {
                show: false,
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["Status"]
};
document.querySelector("#shares").innerHTML = " ";
var chart2 = new ApexCharts(document.querySelector("#shares"), options2);
chart2.render();
function Shares() {
    chart2.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)"],
    })
};
/* shares chart*/
/* projects chart*/
var options = {
    chart: {
        height: 170,
        width: 100,
        type: "radialBar",
    },

    series: [55],
    colors: ["rgba(247, 40, 74, 1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "45%",
                background: "#fff"
            },
            dataLabels: {
                show: false,
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["Status"]
};
document.querySelector("#projects").innerHTML = " ";
var chart = new ApexCharts(document.querySelector("#projects"), options);
chart.render();
/* projects chart*/
/* users111 chart*/
var options = {
    chart: {
        height: 170,
        width: 100,
        type: "radialBar",
    },

    series: [67],
    colors: ["rgba(13, 205, 148, 1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "45%",
                background: "#fff"
            },
            dataLabels: {
                show: false,
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["Status"]
};
document.querySelector("#users111").innerHTML = " ";
var chart = new ApexCharts(document.querySelector("#users111"), options);
chart.render();
/* users111 chart*/

//Spark1
var options4 = {
chart: {
    type: 'area',
    height: 60,
    width: 160,
    sparkline: {
    enabled: true
    },
    dropShadow: {
        enabled: true,
        blur: 3,
        opacity: 0.2,
    }
    },
    stroke: {
        show: true,
        curve: 'smooth',
        lineCap: 'butt',
        colors: undefined,
        width: 2,
        dashArray: 0,
    },
fill: {
    gradient: {
    enabled: false
    }
},
series: [{
    name: 'Total Revenue',
    data: [0, 45, 54, 38, 56, 24, 65, 31, 37, 39, 62, 51, 35, 41, 35, 27, 93, 53, 61, 27, 54, 43, 19, 46]
}],
grid: {
    show: false,xaxis: {
        lines: {
            show: false
        }
    },   
    yaxis: {
        lines: {
            show: false
        }
    },  
},
yaxis: {
    min: 0,
},
colors: ['#3366ff'],

}
document.querySelector("#spark1").innerHTML = " ";
var spark1 = new ApexCharts(document.querySelector("#spark1"), options4);
spark1.render();
function Spark1() {
    spark1.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)"],
    })
};
// var spark1 = new ApexCharts(document.querySelector("#spark1"), spark1);
// spark1.render();
//Spark1

//Spark2
var spark2 = {
chart: {
    type: 'area',
    height: 60,
    width: 160,
    sparkline: {
    enabled: true
    },
    dropShadow: {
        enabled: true,
        blur: 3,
        opacity: 0.2,
    }
    },
    stroke: {
        show: true,
        curve: 'smooth',
        lineCap: 'butt',
        colors: undefined,
        width: 2,
        dashArray: 0,
    },
    fill: {
    gradient: {
    enabled: false
    }
},
series: [{
    name: 'Unique Visitors',
    data: [0, 45, 93, 53, 61, 27, 54, 43, 19, 46, 54, 38, 56, 24, 65, 31, 37, 39, 62, 51, 35, 41, 35, 27, ]
}],
yaxis: {
    min: 0
},
colors: ['#2dce89'],

}
var spark2 = new ApexCharts(document.querySelector("#spark2"), spark2);
spark2.render();
//Spark2

//Spark3
var spark3 = {
chart: {
    type: 'area',
    height: 60,
    width: 160,
    sparkline: {
    enabled: true
    },
    dropShadow: {
        enabled: true,
        blur: 3,
        opacity: 0.2,
    }
    },
    stroke: {
        show: true,
        curve: 'smooth',
        lineCap: 'butt',
        colors: undefined,
        width: 2,
        dashArray: 0,
    },
    fill: {
    gradient: {
    enabled: false
    }
},
series: [{
    name: 'Expenses',
    data: [0, 35, 41, 35, 27, 93, 53, 61, 27, 54, 43, 19, 46,45, 54, 38, 56, 24, 65, 31, 37, 39, 62, 51]
}],
yaxis: {
    min: 0
},
colors: ['#ff5b51'],

}
var spark3 = new ApexCharts(document.querySelector("#spark3"), spark3);
spark3.render();
//Spark3

//sparklinebar1
var sparklinebar1 = {
    series: [{
    data: [1, 4, 2, 4, 5, 4,5,2,4,5,1,4,5,4,2,5,4,2,4,5,4,5,4,2,5,4,2,4,5]
  }],
    chart: {
    type: 'bar',
    width: 380,
    height: 40,
    sparkline: {
      enabled: true
    }
  },
  plotOptions: {
    bar: {
      columnWidth: '38%'
    }
  },
  fill: {
    opacity: 1
},
  labels: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  xaxis: {
    crosshairs: {
      width: 1
    },
  },
  colors: ['#fa057a'],
  tooltip: {
    fixed: {
      enabled: false
    },
    x: {
      show: false
    },
    y: {
      title: {
        formatter: function (seriesName) {
          return ''
        }
      }
    },
    marker: {
      show: false
    }
  }
  };

var sparklinebar1 = new ApexCharts(document.querySelector("#sparklinebar1"), sparklinebar1);
sparklinebar1.render();
//sparklinebar1

//sparklinebar2
var sparklinebar2 = {
    series: [{
    data: [1, 4, 2, 4, 5, 4,5,2,4,5,1,4,5,4,2,5,4,2,4,5,4,5,4,2,5,4,2,4,5]
  }],
    chart: {
    type: 'bar',
    width: 380,
    height: 40,
    sparkline: {
      enabled: true
    }
  },
  plotOptions: {
    bar: {
      columnWidth: '38%'
    }
  },
  fill: {
    opacity: 1
},
  labels: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  xaxis: {
    crosshairs: {
      width: 1
    },
  },
  colors: ['#f7346b'],
  tooltip: {
    fixed: {
      enabled: false
    },
    x: {
      show: false
    },
    y: {
      title: {
        formatter: function (seriesName) {
          return ''
        }
      }
    },
    marker: {
      show: false
    }
  }
  };

var sparklinebar2 = new ApexCharts(document.querySelector("#sparklinebar2"), sparklinebar2);
sparklinebar2.render();
//sparklinebar2

//sparklinebar3
var sparklinebar3 = {
    series: [{
    data: [1, 4, 2, 4, 5, 4,5,2,4,5,1,4,5,4,2,5,4,2,4,5,4,5,4,2,5,4,2,4,5]
  }],
    chart: {
    type: 'bar',
    width: 380,
    height: 40,
    sparkline: {
      enabled: true
    }
  },
  plotOptions: {
    bar: {
      columnWidth: '38%'
    }
  },
  fill: {
    opacity: 1
},
  labels: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  xaxis: {
    crosshairs: {
      width: 1
    },
  },
  colors: ['#2dce89'],
  tooltip: {
    fixed: {
      enabled: false
    },
    x: {
      show: false
    },
    y: {
      title: {
        formatter: function (seriesName) {
          return ''
        }
      }
    },
    marker: {
      show: false
    }
  }
  };

var sparklinebar3 = new ApexCharts(document.querySelector("#sparklinebar3"), sparklinebar3);
sparklinebar3.render();
//sparklinebar3

//sparklinebar4
var sparklinebar4 = {
    series: [{
    data: [1, 4, 2, 4, 5, 4,5,2,4,5,1,4,5,4,2,5,4,2,4,5,4,5,4,2,5,4,2,4,5]
  }],
    chart: {
    type: 'bar',
    width: 380,
    height: 40,
    sparkline: {
      enabled: true
    }
  },
  plotOptions: {
    bar: {
      columnWidth: '38%'
    }
  },
  fill: {
    opacity: 1
},
  labels: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  xaxis: {
    crosshairs: {
      width: 1
    },
  },
  colors: ['#45aaf2'],
  tooltip: {
    fixed: {
      enabled: false
    },
    x: {
      show: false
    },
    y: {
      title: {
        formatter: function (seriesName) {
          return ''
        }
      }
    },
    marker: {
      show: false
    }
  }
  };

var sparklinebar4 = new ApexCharts(document.querySelector("#sparklinebar4"), sparklinebar4);
sparklinebar4.render();
//sparklinebar4

 /* Start::CryptoChart */
 var CryptoChart = {
    chart: {
      type: "area",
      height: 70,
      sparkline: {
        enabled: true,
      },
      dropShadow: {
        enabled: true,
        enabledOnSeries: undefined,
        top: 0,
        left: 0,
        blur: 1,
        color: "#fff",
        opacity: 0.05,
      },
    },
    stroke: {
      show: true,
      curve: "smooth",
      lineCap: "butt",
      colors: undefined,
      width: 2.5,
      ltcArray: 0,
    },
    fill: {
      gradient: {
        enabled: false,
      },
    },
    series: [
      {
        name: "Value",
        data: [80, 60, 77, 64, 71, 64],
      },
    ],
    yaxis: {
      min: 0,
      show: false,
    },
    xaxis: {
      axisBorder: {
        show: false,
      },
    },
    yaxis: {
      axisBorder: {
        show: false,
      },
    },
    colors: ["rgba(51, 102, 255,0.6)"],
  };

  var CryptoChart = new ApexCharts(document.querySelector("#CryptoChart"), CryptoChart);
  CryptoChart.render();
/* End:: CryptoChart */ 

 /* Start::CryptoChart1 */
 var CryptoChart1 = {
    chart: {
      type: "area",
      height: 70,
      sparkline: {
        enabled: true,
      },
      dropShadow: {
        enabled: true,
        enabledOnSeries: undefined,
        top: 0,
        left: 0,
        blur: 1,
        color: "#fff",
        opacity: 0.05,
      },
    },
    stroke: {
      show: true,
      curve: "smooth",
      lineCap: "butt",
      colors: undefined,
      width: 2.5,
      ltcArray: 0,
    },
    fill: {
      gradient: {
        enabled: false,
      },
    },
    series: [
      {
        name: "Value",
        data: [58, 67, 50, 67, 85, 67, 85],
      },
    ],
    yaxis: {
      min: 0,
      show: false,
    },
    xaxis: {
      axisBorder: {
        show: false,
      },
    },
    yaxis: {
      axisBorder: {
        show: false,
      },
    },
    colors: ["rgba(51, 102, 255,0.6)"],
  };

  var CryptoChart1 = new ApexCharts(document.querySelector("#CryptoChart1"), CryptoChart1);
  CryptoChart1.render();
/* End:: CryptoChart1 */ 

 /* Start::CryptoChart2 */
 var CryptoChart2 = {
    chart: {
      type: "area",
      height: 70,
      sparkline: {
        enabled: true,
      },
      dropShadow: {
        enabled: true,
        enabledOnSeries: undefined,
        top: 0,
        left: 0,
        blur: 1,
        color: "#fff",
        opacity: 0.05,
      },
    },
    stroke: {
      show: true,
      curve: "smooth",
      lineCap: "butt",
      colors: undefined,
      width: 2.5,
      ltcArray: 0,
    },
    fill: {
      gradient: {
        enabled: false,
      },
    },
    series: [
      {
        name: "Value",
        data: [70, 77, 60, 77, 56, 80, 60],
      },
    ],
    yaxis: {
      min: 0,
      show: false,
    },
    xaxis: {
      axisBorder: {
        show: false,
      },
    },
    yaxis: {
      axisBorder: {
        show: false,
      },
    },
    colors: ["rgba(51, 102, 255,0.6)"],
  };

  var CryptoChart2 = new ApexCharts(document.querySelector("#CryptoChart2"), CryptoChart2);
  CryptoChart2.render();
/* End:: CryptoChart2 */ 

 /* Start::CryptoChart3 */
 var CryptoChart3 = {
    chart: {
      type: "area",
      height: 70,
      sparkline: {
        enabled: true,
      },
      dropShadow: {
        enabled: true,
        enabledOnSeries: undefined,
        top: 0,
        left: 0,
        blur: 1,
        color: "#fff",
        opacity: 0.05,
      },
    },
    stroke: {
      show: true,
      curve: "smooth",
      lineCap: "butt",
      colors: undefined,
      width: 2.5,
      ltcArray: 0,
    },
    fill: {
      gradient: {
        enabled: false,
      },
    },
    series: [
      {
        name: "Value",
        data: [64, 72, 80, 64, 75, 60, 77],
      },
    ],
    yaxis: {
      min: 0,
      show: false,
    },
    xaxis: {
      axisBorder: {
        show: false,
      },
    },
    yaxis: {
      axisBorder: {
        show: false,
      },
    },
    colors: ["rgba(51, 102, 255,0.6)"],
  };

  var CryptoChart3 = new ApexCharts(document.querySelector("#CryptoChart3"), CryptoChart3);
  CryptoChart3.render();
/* End:: CryptoChart3 */ 