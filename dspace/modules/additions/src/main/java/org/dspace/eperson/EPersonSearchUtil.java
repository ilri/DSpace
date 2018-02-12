package org.dspace.eperson;

import java.sql.*;
import java.util.*;
import org.apache.commons.lang.*;
import org.dspace.core.*;
import org.dspace.storage.rdbms.*;

/**
 * User: kevin (kevin at atmire.com)
 * Date: 26/11/12
 * Time: 09:28
 */
public class EPersonSearchUtil {

    /**
     * Find the epeople that match the search query across firstname, lastname or email.
     * This method also allows offsets and limits for pagination purposes.
     *
     * @param context DSpace context
     * @param offset  Inclusive offset
     * @param limit   Maximum number of matches returned
     * @return array of EPerson objects
     */
    public static SearchResult findSet(Context context, int sort, String direction, int offset, int limit, HashSet<Integer> subset)
            throws SQLException {

        StringBuilder queryBuf = new StringBuilder();
        queryBuf.append("SELECT * FROM eperson_metadata  ");
        if (subset != null) {
            if(subset.isEmpty()){
                return new SearchResult(new EPerson[0],0);
            }
            queryBuf.append("WHERE eperson_id in (");
            for (Iterator<Integer> iterator = subset.iterator(); iterator.hasNext(); ) {
                Integer next = iterator.next();
                queryBuf.append(next);
                if (iterator.hasNext()) queryBuf.append(",");
            }
            queryBuf.append(") ");
        }
        String orderBy = null;
        String s;

        switch (sort) {
            case EPerson.ID:
                s = "eperson_id";
                break;

            case EPerson.EMAIL:
                s = "email";
                break;

            case EPerson.LANGUAGE:
                s = "language";
                break;
            case EPerson.NETID:
                s = "netid";
                break;

            default:
                s = "lastname";
        }
        orderBy = " ORDER BY " + s + " " + direction + " ";
        queryBuf.append(orderBy);


        // Add offset and limit restrictions - Oracle requires special code
        if (DatabaseManager.isOracle()) {
            // First prepare the query to generate row numbers
            if (limit > 0 || offset > 0) {
                queryBuf.insert(0, "SELECT /*+ FIRST_ROWS(n) */ rec.*, ROWNUM rnum  FROM (");
                queryBuf.append(") ");
            }

            // Restrict the number of rows returned based on the limit
            if (limit > 0) {
                queryBuf.append("rec WHERE rownum<=? ");
                // If we also have an offset, then convert the limit into the maximum row number
                if (offset > 0) {
                    limit += offset;
                }
            }

            // Return only the records after the specified offset (row number)
            if (offset > 0) {
                queryBuf.insert(0, "SELECT * FROM (");
                queryBuf.append(") WHERE rnum>?");
            }
        } else {
            if (limit > 0) {
                queryBuf.append(" LIMIT ? ");
            }

            if (offset > 0) {
                queryBuf.append(" OFFSET ? ");
            }
        }

        String dbquery = queryBuf.toString();


        // Create the parameter array, including limit and offset if part of the query
        Object[] paramArr = new Object[]{};
        if (limit > 0 && offset > 0) {
            paramArr = new Object[]{limit, offset};
        } else if (limit > 0) {
            paramArr = new Object[]{limit};
        } else if (offset > 0) {
            paramArr = new Object[]{offset};
        }

        // Get all the epeople that match the query
        TableRowIterator rows = DatabaseManager.query(context,
                dbquery, paramArr);
        try {
            List<TableRow> epeopleRows = rows.toList();
            EPerson[] epeople = new EPerson[epeopleRows.size()];

            for (int i = 0; i < epeopleRows.size(); i++) {
                TableRow row = (TableRow) epeopleRows.get(i);

                // First check the cache
                EPerson fromCache = (EPerson) context.fromCache(EPerson.class, row
                        .getIntColumn("eperson_id"));

                if (fromCache != null) {
                    epeople[i] = fromCache;
                } else {
                    epeople[i] = new EPerson(context, row);
                }
            }
            if(DatabaseManager.isOracle())
            {
                //Remove our query wrapper
                dbquery = StringUtils.replace(dbquery, "SELECT /*+ FIRST_ROWS(n) */ rec.*, ROWNUM rnum  FROM (", "").replace(") rec WHERE rownum<=? ", "");
            }

            dbquery = dbquery.replace("*", "count(eperson_id) as ct").replace(orderBy, "").replace(" OFFSET ? ", "").replace(" LIMIT ? ", "");

            return new SearchResult(epeople, DatabaseManager.querySingle(context, dbquery).getLongColumn("ct"));
        } finally {
            if (rows != null) {
                rows.close();
            }
        }
    }

    /**
     * Find the epeople that match the search query across firstname, lastname or email.
     * This method also allows offsets and limits for pagination purposes.
     *
     * @param context DSpace context
     * @param query   The search string
     * @param offset  Inclusive offset
     * @param limit   Maximum number of matches returned
     * @return array of EPerson objects
     */
    public static SearchResult search(Context context, String query, int sort, String direction, int offset, int limit, HashSet<Integer> subset)
            throws SQLException {

        String params = "%" + query.toLowerCase() + "%";
        StringBuffer queryBuf = new StringBuffer();
        queryBuf.append("SELECT * FROM eperson_metadata WHERE eperson_id = ? OR ");

        if (subset == null)
            queryBuf.append("LOWER(firstname) LIKE LOWER(?) OR LOWER(lastname) LIKE LOWER(?) OR LOWER(email) LIKE LOWER(?)");
        else if(subset.isEmpty()){
            return new SearchResult(new EPerson[0],0L);
        }
        else {
            queryBuf.append("(LOWER(firstname) LIKE LOWER(?) OR LOWER(lastname) LIKE LOWER(?) OR LOWER(email) LIKE LOWER(?)) AND eperson_id in (");
            for (Iterator<Integer> iterator = subset.iterator(); iterator.hasNext(); ) {
                Integer next = iterator.next();
                queryBuf.append(next);
                if (iterator.hasNext()) queryBuf.append(",");
            }
            queryBuf.append(") ");
        }

        String orderBy = null;
        String s;

        switch (sort) {
            case EPerson.ID:
                s = "eperson_id";
                break;

            case EPerson.EMAIL:
                s = "email";
                break;

            case EPerson.LANGUAGE:
                s = "language";
                break;
            case EPerson.NETID:
                s = "netid";
                break;

            default:
                s = "lastname";
        }
        orderBy = " ORDER BY " + s + " " + direction + " ";
        queryBuf.append(orderBy);


        // Add offset and limit restrictions - Oracle requires special code
        if (DatabaseManager.isOracle()) {
            // First prepare the query to generate row numbers
            if (limit > 0 || offset > 0) {
                queryBuf.insert(0, "SELECT /*+ FIRST_ROWS(n) */ rec.*, ROWNUM rnum  FROM (");
                queryBuf.append(") ");
            }

            // Restrict the number of rows returned based on the limit
            if (limit > 0) {
                queryBuf.append("rec WHERE rownum<=? ");
                // If we also have an offset, then convert the limit into the maximum row number
                if (offset > 0) {
                    limit += offset;
                }
            }

            // Return only the records after the specified offset (row number)
            if (offset > 0) {
                queryBuf.insert(0, "SELECT * FROM (");
                queryBuf.append(") WHERE rnum>?");
            }
        } else {
            if (limit > 0) {
                queryBuf.append(" LIMIT ? ");
            }

            if (offset > 0) {
                queryBuf.append(" OFFSET ? ");
            }
        }

        String dbquery = queryBuf.toString();

        // When checking against the eperson-id, make sure the query can be made into a number
        Integer int_param;
        try {
            int_param = Integer.valueOf(query);
        } catch (NumberFormatException e) {
            int_param = -1;
        }

        // Create the parameter array, including limit and offset if part of the query
        Object[] paramArr = new Object[]{int_param, params, params, params};
        if (limit > 0 && offset > 0) {
            paramArr = new Object[]{int_param, params, params, params, limit, offset};
        } else if (limit > 0) {
            paramArr = new Object[]{int_param, params, params, params, limit};
        } else if (offset > 0) {
            paramArr = new Object[]{int_param, params, params, params, offset};
        }

        // Get all the epeople that match the query
        TableRowIterator rows = DatabaseManager.query(context,
                dbquery, paramArr);
        try {
            List<TableRow> epeopleRows = rows.toList();
            EPerson[] epeople = new EPerson[epeopleRows.size()];

            for (int i = 0; i < epeopleRows.size(); i++) {
                TableRow row = (TableRow) epeopleRows.get(i);

                // First check the cache
                EPerson fromCache = (EPerson) context.fromCache(EPerson.class, row
                        .getIntColumn("eperson_id"));

                if (fromCache != null) {
                    epeople[i] = fromCache;
                } else {
                    epeople[i] = new EPerson(context, row);
                }
            }
            if(DatabaseManager.isOracle())
            {
                //Remove our query wrapper
                dbquery = StringUtils.replace(dbquery, "SELECT /*+ FIRST_ROWS(n) */ rec.*, ROWNUM rnum  FROM (", "").replace(") rec WHERE rownum<=? ", "");
            }

            dbquery = dbquery.replace("*", "count(eperson_id) as ct").replace(orderBy, "").replace(" OFFSET ? ", "").replace(" LIMIT ? ", "");
            return new SearchResult(epeople, DatabaseManager.querySingle(context, dbquery, new Object[]{int_param, params, params, params}).getLongColumn("ct"));
        } finally {
            if (rows != null) {
                rows.close();
            }
        }
    }

    public static class SearchResult {
        public final EPerson epersons[];
        public final long count;

        public SearchResult(EPerson[] epersons, long count) {
            this.epersons = epersons;
            this.count = count;
        }
    }
}