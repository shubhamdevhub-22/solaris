class TableCsv {
    /**
     * @param {HTMLTableElement} root The table element which will display the CSV data.
     */
    constructor(root) {
      this.root = root;
    }
  
    /**
     * Clears existing data in the table and replaces it with new data.
     *
     * @param {string[][]} data A 2D array of data to be used as the table body
     * @param {string[]} headerColumns List of headings to be used
     */
    update(data, headerColumns = []) {
      this.clear();
      this.setHeader(headerColumns);
      this.setBody(data);
    }
  
    /**
     * Clears all contents of the table (incl. the header).
     */
    clear() {
      this.root.innerHTML = "";
    }
  
    /**
     * Sets the table header.
     *
     * @param {string[]} headerColumns List of headings to be used
     */
    setHeader(headerColumns) {
      this.root.insertAdjacentHTML(
        "afterbegin",
        `
              <thead>
                  <tr>
                      ${headerColumns.map((text) => `<th>${text}</th>`).join("")}
                  </tr>
              </thead>
          `
      );
    }
  
    /**
     * Sets the table body.
     *
     * @param {string[][]} data A 2D array of data to be used as the table body
     */

    setBody(data) {
      const rowsHtml = data.map((row, index) => {
        console.log(index)
        if (index<=11) {
            return `
                      <tr>
                          ${row.map((text) => `<td>${text}</td>`).join("")}
                      </tr>
                  `;
        }
      });
  
      this.root.insertAdjacentHTML(
        "beforeend",
        `
              <tbody>
                  ${rowsHtml.join("")}
              </tbody>
          `
      );
    }
  }
  
  const tableRoot = document.querySelector("#csvRoot");
  const id_csv_file = document.querySelector("#id_csv_file");
  const tableCsv = new TableCsv(tableRoot);
  
  id_csv_file.addEventListener("change", (e) => {
    Papa.parse(id_csv_file.files[0], {
      delimiter: ",",
      skipEmptyLines: true,
      complete: (results) => {
      	console.log('results:', results)
        tableCsv.update(results.data.slice(1), results.data[0]);
      }

    
    });
  });


  