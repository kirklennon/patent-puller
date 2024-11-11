# patent-puller
Django web application for pulling patent information. User enters a patent number and patent-puller uses the USPTO assignment API to extract the *current* assignee from the XML assignment data. The original version used Beautiful Soup to scrape the title, abstract, and inventors from the individual patent's page found using a USPTO number search, but that straightforward indvidual information page was discontinued and replaced with a convoluted JavaScript-heavy search tool. Thankfully the USPTO also has a [poorly-publicized API](https://search.patentsview.org/docs/docs/Search%20API/SearchAPIReference) that makes the same information availble as JSON.
## 2024 Update
The original version of this was implemented using Django's built-in forms feature. I reimplemented it as a single webpage that uses Javascript to call a JSON API, which is then parsed and displayed in a table.
## Currently implemented features
The user can multiple line-separated patents in a textarea field. Each patent number  is validated for formatting. Inventor names are reformatted from "Last First Middle" into standard "First Middle Last" name order and, if more than one, are concatenated into a comma-separated string containing all inventors. 
## Reassignment data inaccuracies
The assignment data is given in reverse-chronological order but is very messy and often incomplete or contains errors and sometimes separate entries with corrections. The patent puller looks for the first assignment entry in the list, which is usually the most recent, which is treated as the presumptive current assignee. It also searches for name change entries to the presumptive assignee, but doesn't catch every edge case. It does not currently search for mergers, which can result in a change to the assignee. The following are some specific assignment types that are not accounted for:
 * "MERGER (SEE DOCUMENT FOR DETAILS)"
 * "ASSET TRANSFER COVENANT" (example: 7,557,711)
